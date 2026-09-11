"""引擎 · 模块四：差异打标（diff_tag）。

两条输入通道共用本模块：
  - 全量通道：不做 diff，所有测试点标 `全量`；
  - 增量通道：`git diff base..target` → 变更文件集 + hunk 行区间 → 命中即标 `更新`。

安全约束（沿用 legacy 的实战教训）：
  - 先做**仓库可用性校验**：若 `.git` 向上逃逸到祖先仓库（孤儿 `.git` 目录），
    一律阻断，避免 `git -C <target>` 误伤本项目仓库、或拿到错误的 diff；
  - git 调用一律走参数列表（不经 shell），并设超时。
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from core.enums import Tag
from core.errors import WorkspaceEscapeBlocked


_GIT_TIMEOUT = 60
# @@ -old_start,old_len +new_start,new_len @@
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")


def run_git(
    repo: str | Path, args: list[str], *, timeout: int = _GIT_TIMEOUT
) -> subprocess.CompletedProcess[str]:
    """在指定仓库执行 git 命令（参数列表，不启用 shell）。"""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def git_toplevel(repo: str | Path) -> str | None:
    """返回 git 顶层目录；非仓库返回 None。"""
    try:
        cp = run_git(repo, ["rev-parse", "--show-toplevel"])
    except (OSError, subprocess.SubprocessError):
        return None
    if cp.returncode != 0:
        return None
    return cp.stdout.strip() or None


def repo_escape_blocked(repo: str | Path) -> bool:
    """判断目标目录的 git 顶层是否**越过了**目标目录本身（逃逸）。

    典型场景：目标目录里只有一个孤儿 `.git`，git 会向上找到父仓库，
    导致 diff 拿到的是父仓库的变更——必须阻断。
    """
    top = git_toplevel(repo)
    if not top:
        return False
    target = Path(repo).resolve()
    try:
        top_path = Path(top).resolve()
    except OSError:
        return True
    return top_path != target and top_path not in target.parents


def refs_available(repo: str | Path, *refs: str) -> bool:
    """给定的 base/target ref 是否**逐个**都能解析为 commit。

    注意：`git rev-parse --verify` 一次只接受**一个** revision，
    传多个会以 "Needed a single revision" 失败（rc=1）——必须逐个校验，
    否则任何增量运行都会被误判为「ref 不可解析」而静默降级为全量。
    """
    if not refs:
        return False
    for ref in refs:
        try:
            cp = run_git(repo, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
        except (OSError, subprocess.SubprocessError):
            return False
        if cp.returncode != 0:
            return False
    return True


def compute_changed_files(repo: str | Path, base: str, target: str) -> set[str]:
    """返回变更文件集合（正斜杠相对路径）。"""
    try:
        cp = run_git(repo, ["diff", "--name-only", f"{base}..{target}"])
    except (OSError, subprocess.SubprocessError):
        return set()
    if cp.returncode != 0:
        return set()
    return {ln.strip().replace("\\", "/") for ln in cp.stdout.splitlines() if ln.strip()}


def compute_diff_hunks(
    repo: str | Path, base: str, target: str
) -> dict[str, list[tuple[int, int]]]:
    """返回 {相对路径: [(新文件起始行, 行数), ...]}。"""
    try:
        cp = run_git(repo, ["diff", "-U0", f"{base}..{target}"])
    except (OSError, subprocess.SubprocessError):
        return {}
    if cp.returncode != 0:
        return {}

    hunks: dict[str, list[tuple[int, int]]] = {}
    current: str | None = None
    for line in cp.stdout.splitlines():
        m = _DIFF_FILE_RE.match(line)
        if m:
            current = m.group(1).replace("\\", "/")
            hunks.setdefault(current, [])
            continue
        if current is None:
            continue
        hm = _HUNK_RE.match(line)
        if hm:
            start = int(hm.group(1))
            length = int(hm.group(2)) if hm.group(2) is not None else 1
            hunks[current].append((start, length))
    return hunks


# ---------------------------------------------------------------- 打标
@dataclass
class DiffContext:
    """增量上下文（全量通道传空即退化为「全量」）。"""

    changed_files: set[str] = field(default_factory=set)
    hunks: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    aligned: bool = False  # 是否已按 target ref 对齐行号

    @property
    def is_incremental(self) -> bool:
        return bool(self.changed_files)


def tag_of_rel(rel: str, ctx: DiffContext) -> str:
    """文件级打标：文件在变更集内即「更新」。"""
    if not ctx.is_incremental:
        return Tag.FULL.value
    norm = (rel or "").replace("\\", "/")
    if norm in ctx.changed_files:
        return Tag.UPDATE.value
    base = norm.rsplit("/", 1)[-1]
    for changed in ctx.changed_files:
        if changed.rsplit("/", 1)[-1] == base:
            return Tag.UPDATE.value
    return Tag.FULL.value


def tag_of_symbol(rel: str, start_line: int, end_line: int, ctx: DiffContext) -> str:
    """符号级打标：符号行区间 ∩ hunk 区间命中即「更新」；无 hunk 数据则降级到文件级。"""
    if not ctx.is_incremental:
        return Tag.FULL.value
    norm = (rel or "").replace("\\", "/")
    spans = ctx.hunks.get(norm)
    if not spans:
        return tag_of_rel(norm, ctx)
    for start, length in spans:
        hunk_end = start + max(length, 1) - 1
        if start_line <= hunk_end and end_line >= start:
            return Tag.UPDATE.value
    return Tag.FULL.value


def build_context(repo: str | Path, base: str | None, target: str | None) -> DiffContext:
    """构造差异上下文（含安全校验）。

    - base/target 为空 → 全量通道（返回空上下文）
    - 仓库逃逸 → 抛 RepoEscapeBlockedError
    - ref 不可解析 → 抛 ValueError（调用方决定是否降级全量）
    """
    if not base or not target:
        return DiffContext()
    if repo_escape_blocked(repo):
        raise WorkspaceEscapeBlocked(f"{repo} 的 git 顶层逃逸到祖先目录，已阻断")
    if not refs_available(repo, base, target):
        raise ValueError(f"ref 不可解析：{base} / {target}")
    return DiffContext(
        changed_files=compute_changed_files(repo, base, target),
        hunks=compute_diff_hunks(repo, base, target),
        aligned=True,
    )


def base_ref_of(repo: str | Path, branch: str = "HEAD") -> str | None:
    """取工作树模式下用于对比的基线 ref。"""
    try:
        cp = run_git(repo, ["rev-parse", "--verify", "--quiet", branch])
    except (OSError, subprocess.SubprocessError):
        return None
    return branch if cp.returncode == 0 else None


def is_repo(path: str | Path) -> bool:
    """目录本身是否为 git 仓库（`.git` 存在且未被逃逸）。"""
    p = Path(path)
    if not (p / ".git").exists():
        return False
    return not repo_escape_blocked(p)


def normalize_rel(rel: str) -> str:
    return os.path.normpath(rel).replace("\\", "/") if rel else ""
