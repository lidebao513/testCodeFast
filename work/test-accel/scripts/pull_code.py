"""拉取代码（qa-code-pull）独立模块：与「测试点」skill 完全解耦、互不依赖。

职责（单一、自包含）：
  1. 目标仓库缺失 → 克隆（优先 codeup 直连 + protocol.version=0，避免代理拖慢/失败）；
  2. 仓库为浅克隆 → 加深历史（fetch --deepen，解决 git diff 失真）；
  3. 更新远端并确认 base / target 两个 ref 在本地可解析；
  4. 将工作树切到 target（测试点分析的是「工作树」，需与 target 一致）；
  5. 计算 base..target（或工作树相对基线）的变更文件集合，供「测试点」消费。

设计原则：
  - 仅依赖标准库 + subprocess(git)，不 import 任何 qa-test-points / 平台模块；
  - 所有「写仓库 / 网络」操作均 try/except + 短超时包裹，并终止整个进程树
    （git 派生 ssh/agent 孙进程占用管道，普通超时无法回收）；网络不可用时优雅降级；
  - 目标目录三态判定（missing / repo / escape / not_repo）：
      缺失 → 克隆；非 git 目录 → 克隆进入（空目录）或明确报错；git 顶层逃逸到祖先仓库 → 阻断；
  - 进程退出码默认恒为 0（任何异常已在内部捕获并以 status 标注，保证调用方「无报错」）；
    提供 --strict 开关：当 success=False 时非零退出，供需要严格拦截的调用方使用；
  - POSIX 下 URL 内嵌凭据会被剥离并经 GIT_ASKPASS 注入，避免凭据出现在进程 argv；
  - 与 qa-test-points 通过「文件系统契约」通信（本模块写 result JSON，对方按需读取）。

注：本文件为工程内**唯一真源**（已迁自 qa-code-pull 技能目录），技能目录的 pull_code.py
仅为薄壳委托脚本。状态/模式字符串统一由下方 PullStatus / PullMode / FetchStatus 枚举定义，
禁止散落字面量；其对端真值定义于 backend/core/enums.py::PullStatus，由单测守护一致性。
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


# ============ 唯一真源：拉取状态 / 模式枚举 ============
class PullStatus(Enum):
    """拉取结果状态（落盘字符串即 .value）。

    与 backend/core/enums.py::PullStatus 保持逐值一致（运行时零耦合，由单测守护）。
    """

    OK = "ok"
    OK_OFFLINE = "ok_offline"
    CLONE_FAILED = "clone_failed"
    REFS_UNAVAILABLE = "refs_unavailable"
    REPO_ESCAPE_BLOCKED = "repo_escape_blocked"
    CLONE_REQUIRED_NO_URL = "clone_required_no_url"
    TARGET_NOT_EMPTY = "target_not_empty"


class PullMode(Enum):
    """变更集计算模式。"""

    DUAL_REF = "dual_ref"  # base..target 双 ref 对比
    WORKTREE = "worktree"  # 工作树相对 base 提交（含未跟踪新文件）


class FetchStatus(Enum):
    """远端更新 / 加深结果（仅落盘字段 fetch_status，非最终 PullStatus）。"""

    FETCHED = "fetched"
    SKIPPED_OFFLINE = "skipped_offline"
    DEEPEN_FAILED = "deepen_failed"
    WORKTREE = "worktree"
    NONE = "n/a"


# ============ 默认值（可按项目覆盖，环境变量优先） ============
_THIS = Path(__file__).resolve()
_SCRIPTS_DIR = _THIS.parent  # work/test-accel/scripts
_TEST_ACCEL_ROOT = _SCRIPTS_DIR.parent  # work/test-accel
_WORK_ROOT = _TEST_ACCEL_ROOT.parent  # work
# 被测目标默认位于 work/targets/research-agent（相对本文件解析，避免硬编码个人路径）
DEFAULT_LOCAL = str(_WORK_ROOT / "targets" / "research-agent")
# 当前 research-agent 为就地 git init 的真实独立仓库（无 base/target 历史 ref），
# 默认走「工作树相对基线」模式，避免引用已失效的 test-20260906/07 ref。
DEFAULT_BASE = "HEAD"
DEFAULT_TARGET = "WORKTREE"
DEFAULT_DEEPEN = 300
# codeup 走直连快、代理慢；内网 git 用 protocol.version=0 更稳
GIT_PROTOCOL_PREFIX = ["-c", "protocol.version=0"]
# 网络探测 / 网络操作的硬超时（秒）。本机沙箱网络"卡死不报错"，必须短超时 + 杀进程树。
NETWORK_TIMEOUT = 10

# 目录三态判定结果（内部常量，非枚举真值源）
_STATE_MISSING = "missing"
_STATE_REPO = "repo"
_STATE_ESCAPE = "escape"
_STATE_NOT_REPO = "not_repo"


# ============ URL 脱敏 ============
def _mask_url(url: str) -> str:
    """脱敏：隐藏 git URL 中的 userinfo 与查询串/锚点，避免结果文件泄露。

    与旧实现相比的修正：**不再以「是否存在 userinfo」作为剥离查询串的前提**——
    无凭据但带 `?token=...` 的 URL 同样会泄露令牌，故一律剥离 query / fragment。
    非 URL（本地路径、scp 形式 user@host:path）原样返回。
    """
    if not url or "://" not in url:
        return url
    try:
        p = urlparse(url)
    except Exception:  # 解析异常则整体脱敏，绝不抛出
        return re.sub(r"://[^@/\s]+@", "://***@", url)
    netloc = p.hostname or ""
    if p.port:
        netloc = f"{netloc}:{p.port}"
    if not netloc:
        return re.sub(r"://[^@/\s]+@", "://***@", url)
    masked = f"{p.scheme}://{netloc}{p.path or ''}"
    if p.query:
        masked += "?..."  # 查询串可能含 token，不直接暴露
    if p.fragment:
        masked += "#..."
    return masked


# ============ 跨平台进程树终止 ============
def _kill_proc_tree(proc: subprocess.Popen) -> None:
    """终止进程及其子孙进程（git 派生 ssh/agent）。

    - POSIX：start_new_session=True 后可用 killpg 杀进程组；
    - Windows：无 os.killpg，改用 proc.kill()（TerminateProcess），
      并尽量用 taskkill /T 连带子进程。
    用 getattr 探测符号，避免在 Windows 上引用不存在的 os.getpgid / signal.SIGKILL。
    """
    killpg = getattr(os, "killpg", None)
    getpgid = getattr(os, "getpgid", None)
    sigkill = getattr(signal, "SIGKILL", signal.SIGTERM)
    try:
        if killpg is not None and getpgid is not None:
            killpg(getpgid(proc.pid), sigkill)
        else:
            proc.kill()
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:
                pass
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# ============ git 调用封装 ============
def _run_git(local_path: str, args: list[str], timeout: int = 60) -> tuple[int, str]:
    """本地（非网络）git：捕获 stdout，快速返回。

    注意：本函数会执行传入的任何子命令，**并非只读**——checkout -f 等写操作同样走这里；
    网络操作请用 _net_git()。capture_output 会等待子进程收尾，故仅用于不会挂死的本地命令。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", local_path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="ignore",
        )
        return proc.returncode, (proc.stdout or "")
    except Exception:
        return 1, ""


def _net_git(local_path: str, args: list[str], timeout: int = NETWORK_TIMEOUT) -> int:
    """网络 git（ls-remote/fetch 等）。不捕获管道（避免孙进程占用管道挂死），
    超时则杀进程树，返回 returncode（超时记 1）。"""
    try:
        proc = subprocess.Popen(
            ["git", "-C", local_path, *GIT_PROTOCOL_PREFIX, *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_proc_tree(proc)
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        return 1
    except Exception:
        return 1


# ============ 凭据不经 argv（POSIX） ============
_ASKPASS_TEMPLATE = """#!/bin/sh
# 临时 GIT_ASKPASS：仅从环境变量读取，使凭据不出现在进程 argv。
case "$1" in
  *[Uu]sername*) printf '%s' "$GIT_ASKPASS_USER" ;;
  *) printf '%s' "$GIT_ASKPASS_PASS" ;;
esac
"""


@contextmanager
def _credential_env(url: str):
    """产出 (用于 argv 的 URL, 子进程 env)。

    POSIX 下若 URL 内嵌 user:pass@，则剥离为无凭据 URL，并把凭据经临时 GIT_ASKPASS
    脚本 + 环境变量注入（`ps` 不再可见）。非 POSIX 或 URL 无凭据时原样返回 (url, None)。
    任何异常都回退为 (url, None)，绝不因脱敏而中断克隆。
    """
    clean, env, askpass = url, None, ""
    if os.name != "nt" and "://" in url:
        try:
            p = urlparse(url)
            if p.username or p.password:
                netloc = p.hostname or ""
                if p.port:
                    netloc = f"{netloc}:{p.port}"
                rebuilt = f"{p.scheme}://{netloc}{p.path or ''}"
                if p.query:
                    rebuilt += f"?{p.query}"
                if p.fragment:
                    rebuilt += f"#{p.fragment}"
                fd, askpass = tempfile.mkstemp(prefix="qa-askpass-", suffix=".sh")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(_ASKPASS_TEMPLATE)
                os.chmod(askpass, stat.S_IRWXU)
                env = dict(os.environ)
                env["GIT_ASKPASS"] = askpass
                env["GIT_TERMINAL_PROMPT"] = "0"
                env["GIT_ASKPASS_USER"] = p.username or ""
                env["GIT_ASKPASS_PASS"] = p.password or ""
                clean = rebuilt
        except Exception:  # 脱敏失败则回退原样，保证克隆可用
            clean, env, askpass = url, None, ""
    try:
        yield clean, env
    finally:
        if askpass:
            with contextlib.suppress(Exception):
                os.remove(askpass)


# ============ 目录三态判定（防误伤父仓库 / 允许克隆进入） ============
def _git_toplevel(local: str) -> str:
    """返回 git 顶层真实路径；目录不存在或非 git 仓库 / 探测失败返回 ""。"""
    if not os.path.isdir(local):
        return ""
    rc, out = _run_git(local, ["rev-parse", "--show-toplevel"])
    if rc != 0 or not out.strip():
        return ""
    return os.path.realpath(out.strip())


def classify_target(local: str) -> str:
    """目录三态判定，返回 missing / repo / escape / not_repo。

    - missing  : 目录不存在（无 git 语义）→ 可直接克隆；
    - repo     : 目录本身就是 git 仓库**根** → 正常使用；
    - escape   : 目录位于「祖先仓库」内部（toplevel 逃逸到上层）→ 必须阻断，绝不 diff/checkout 父项目；
    - not_repo : 目录存在但不是 git 仓库 → 允许克隆进入（空目录），非空则明确报错。
    """
    if not os.path.isdir(local):
        return _STATE_MISSING
    top = _git_toplevel(local)
    if not top:
        return _STATE_NOT_REPO
    return _STATE_REPO if top == os.path.realpath(local) else _STATE_ESCAPE


def _git_repo_usable(local: str) -> bool:
    """阶段1 的唯一逃逸判定入口：目录须就是 git 仓库根（严格相等语义）。

    与 backend/modules/code_analyzer.py::_git_repo_usable 语义一致（同一判定口径），
    消除此前「脚本宽松 startswith vs 平台严格相等」的双实现漂移。
    """
    return classify_target(local) == _STATE_REPO


def is_shallow(path: str) -> bool:
    rc, out = _run_git(path, ["rev-parse", "--is-shallow-repository"])
    return rc == 0 and out.strip() == "true"


def get_remote_url(path: str) -> str:
    rc, out = _run_git(path, ["config", "--get", "remote.origin.url"])
    return out.strip() if rc == 0 else ""


# ============ 只读权限管控 ============
def _set_readonly(local: str, readonly: bool) -> None:
    """将仓库文件夹（含全部文件/子目录，递归覆盖 .git）设为只读或恢复读写。

    权限管控用途（qa-code-pull）：
      - 拉取代码前            → readonly=True（保护被测代码，防误改）；
      - 执行克隆/fetch/checkout/变更集 → readonly=False（临时读写）；
      - 拉取完成              → readonly=True（立即恢复只读）。
    Windows：kernel32.SetFileAttributesW 逐文件置/清 READONLY 位。
    POSIX：chmod a-w / a+w。任意异常均吞掉，绝不中断拉取流程。
    """
    if not os.path.isdir(local):
        return
    try:
        if os.name == "nt":
            k32 = ctypes.windll.kernel32
            RO = 0x1
            INVALID = 0x7FFFFFFF

            def _one(p: str) -> None:
                cur = k32.GetFileAttributesW(p)
                if cur in (INVALID, -1):
                    return
                if readonly:
                    k32.SetFileAttributesW(p, cur | RO)
                else:
                    k32.SetFileAttributesW(p, cur & ~RO)

            _one(local)
            for root, dirs, files in os.walk(local):
                for nm in dirs:
                    _one(os.path.join(root, nm))
                for nm in files:
                    _one(os.path.join(root, nm))
        else:
            RW_FILE, RW_DIR = 0o644, 0o755

            def _chmod(p: str, is_dir: bool) -> None:
                try:
                    mode = 0o444 if readonly else (RW_DIR if is_dir else RW_FILE)
                    os.chmod(p, mode)
                except Exception:
                    pass

            _chmod(local, True)
            for root, dirs, files in os.walk(local):
                for nm in dirs:
                    _chmod(os.path.join(root, nm), True)
                for nm in files:
                    _chmod(os.path.join(root, nm), False)
    except Exception:
        pass


@contextmanager
def _readonly_guard(local: str):
    """包裹「写仓库」操作：进入时临时放开只读，退出（含异常）立即恢复只读。"""
    try:
        if os.path.isdir(local):
            _set_readonly(local, False)
        yield
    finally:
        if os.path.isdir(local):
            _set_readonly(local, True)


def _cleanup_failed_clone(path: str) -> None:
    """克隆失败可能留下残缺 .git；清理目标目录，避免下次三态判定误判为 repo。
    清理前先放开只读，防止 Windows 下 rmtree 被 READONLY 位拒绝。"""
    try:
        if os.path.isdir(path):
            _set_readonly(path, False)
            shutil.rmtree(path)
    except Exception:
        pass


# ============ 克隆 / 加深 / ref / checkout / 变更集 ============
def clone(url: str, path: str, errors: list, timeout: int = 180) -> bool:
    """克隆仓库（浅克隆起步，更快；后续按需加深）。失败即清理残缺目录。

    POSIX 下若 URL 内嵌凭据，则剥离后经 GIT_ASKPASS 注入，避免 argv 暴露凭据。
    """
    proc = None
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with _credential_env(url) as (clone_url, env):
            proc = subprocess.Popen(
                ["git", *GIT_PROTOCOL_PREFIX, "clone", "--depth", "1", clone_url, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=env,
            )
            rc = proc.wait(timeout=timeout)
        if rc != 0:
            errors.append(f"clone_failed(rc={rc})")
            _cleanup_failed_clone(path)
            return False
        return True
    except subprocess.TimeoutExpired:
        if proc is not None:
            _kill_proc_tree(proc)
        errors.append("clone_timeout")
        _cleanup_failed_clone(path)
        return False
    except Exception as e:
        errors.append(f"clone_error: {e}")
        _cleanup_failed_clone(path)
        return False


def fetch_and_deepen(
    path: str, refs: list[str], deepen: int, errors: list, online: bool = True
) -> str:
    """更新远端并加深历史。返回 FetchStatus 值（fetched / skipped_offline / deepen_failed）。"""
    if not online:
        return FetchStatus.SKIPPED_OFFLINE.value
    if _net_git(path, ["fetch", "--tags", "origin"]) != 0:
        return FetchStatus.SKIPPED_OFFLINE.value
    deepened_ok = True
    if is_shallow(path):
        if _net_git(path, ["fetch", "--deepen", str(deepen), "origin"]) != 0:
            deepened_ok = False
        for ref in refs:
            _net_git(path, ["fetch", "origin", ref])
    return FetchStatus.FETCHED.value if deepened_ok else FetchStatus.DEEPEN_FAILED.value


def ensure_refs(path: str, refs: list[str], errors: list, online: bool = True) -> bool:
    """确保 base / target 在本地可解析；不可解析则尝试 fetch 对应 ref。"""
    ok = True
    for ref in refs:
        rc, _ = _run_git(path, ["rev-parse", "--quiet", ref])
        if rc == 0:
            continue
        if not online:
            errors.append(f"ref_unavailable_offline: {ref}")
            ok = False
            continue
        if _net_git(path, ["fetch", "origin", ref]) != 0 and (
            _net_git(path, ["fetch", "origin", f"+refs/heads/{ref}:refs/remotes/origin/{ref}"]) != 0
        ):
            errors.append(f"ref_unavailable: {ref}")
            ok = False
    return ok


def checkout(path: str, ref: str, errors: list) -> str:
    """将工作树切换到 target。已在其上则视为 no-op。"""
    rc, out = _run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
    cur = out.strip()
    if cur == ref:
        return ref
    rc, _ = _run_git(path, ["checkout", "-f", ref], timeout=120)
    if rc != 0:
        errors.append(f"checkout_failed: {ref}")
        return cur
    return ref


def changed_files(path: str, base: str, target: str) -> list:
    rc, out = _run_git(path, ["diff", "--name-only", f"{base}..{target}"], timeout=120)
    if rc != 0:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def changed_vs_worktree(path: str, base: str) -> list:
    """相对 base 提交，列出工作树（含未提交修改 + 未跟踪/新增/重命名新路径）的变更集合。"""
    tracked: list = []
    rc, out = _run_git(path, ["diff", "--name-only", base], timeout=120)
    if rc == 0:
        tracked = [ln.strip() for ln in out.splitlines() if ln.strip()]
    untracked: list = []
    rc2, out2 = _run_git(path, ["status", "--porcelain"], timeout=120)
    if rc2 == 0:
        for ln in out2.splitlines():
            if len(ln) < 4:
                continue
            code = ln[:2]
            rest = ln[3:]
            # 重命名/复制：porcelain v1 形如 "R  old -> new"，须取**新**路径
            if code[0] in ("R", "C") and " -> " in rest:
                rest = rest.split(" -> ", 1)[1]
            f = rest.strip()
            if len(f) >= 2 and f[0] == '"' and f[-1] == '"':
                f = f[1:-1]  # git 对含特殊字符的路径会加引号
            if code in ("??", "A ", "AM", "R ", "C ") and f and f not in tracked:
                untracked.append(f)
    return tracked + untracked


def sha(path: str, ref: str) -> str:
    rc, out = _run_git(path, ["rev-parse", "--short", ref])
    return out.strip() if rc == 0 else ""


def _detect_online(local: str, url: str, state: str):
    """返回 True/False；None 表示既无可用仓库、也无 url，无法克隆。"""
    if state == _STATE_REPO:
        return _net_git(local, ["ls-remote", "--heads", "origin"]) == 0
    if url:
        return True
    return None


def _is_worktree_mode(target: str) -> bool:
    """WORKTREE 模式仅由显式 sentinel 触发。

    注：不再把 "HEAD" 当作工作树别名——那会让 target_sha 恒空且语义含糊；
    如需分析当前工作树请显式传 WORKTREE（或缺省）。
    """
    return target.strip().upper() in ("", "WORKTREE")


def _is_empty_dir(path: str) -> bool:
    try:
        return not os.listdir(path)
    except Exception:
        return False


# ============ 主流程 ============
def pull(url: str, local: str, base: str, target: str, deepen: int, out_json: str) -> dict:
    errors: list = []
    result: dict[str, Any] = {
        "status": PullStatus.OK.value,
        "success": True,
        "mode": "",
        "url": _mask_url(url or ""),
        "local_path": local,
        "base": base,
        "target": target,
        "shallow": None,
        "deepened": False,
        "fetch_status": FetchStatus.NONE.value,
        "checked_out": "",
        "base_sha": "",
        "target_sha": "",
        "changed_count": 0,
        "changed_files": [],
        "errors": errors,
    }

    # 阶段0：目录三态判定（missing / repo / escape / not_repo）
    state = classify_target(local)
    dir_existed = state != _STATE_MISSING

    # 阶段0-escape：防误伤父仓库（硬性安全网）——目录位于祖先仓库内部
    if state == _STATE_ESCAPE:
        _set_readonly(local, True)  # 拉取前先置只读，保护被测代码
        result["status"] = PullStatus.REPO_ESCAPE_BLOCKED.value
        result["success"] = False
        result["errors"].append(
            f"目录 {local} 位于祖先 git 仓库内部（git 顶层逃逸到上层），已阻断以防误改父项目；"
            f"请在该目录内 git init 或删除后重新克隆为独立仓库"
        )
        result["perm"] = {
            "readonly_before_pull": True,
            "restored_after_pull": True,
            "note": "目录已存在，拉取前已置只读；未执行任何写操作",
        }
        _dump(result, out_json)
        return result

    if state == _STATE_REPO:
        _set_readonly(local, True)  # 拉取前先置只读，保护被测代码

    # 阶段0-not_repo：目录已存在但不是 git 仓库
    if state == _STATE_NOT_REPO:
        if not url:
            result["status"] = PullStatus.CLONE_REQUIRED_NO_URL.value
            result["success"] = False
            result["errors"].append(
                f"目录 {local} 已存在但不是 git 仓库，且未提供仓库地址，无法克隆"
            )
            result["perm"] = {
                "readonly_before_pull": False,
                "restored_after_pull": False,
                "note": "非 git 目录且无 url，未执行任何写操作",
            }
            _dump(result, out_json)
            return result
        if not _is_empty_dir(local):
            result["status"] = PullStatus.TARGET_NOT_EMPTY.value
            result["success"] = False
            result["errors"].append(
                f"目录 {local} 已存在且非空，git clone 无法写入非空目录；请清空该目录或改用其他路径"
            )
            result["perm"] = {
                "readonly_before_pull": False,
                "restored_after_pull": False,
                "note": "非空且非 git 目录，未执行任何写操作",
            }
            _dump(result, out_json)
            return result

    # 阶段0b：离线探测
    online = _detect_online(local, url, state)
    if online is None:
        result["status"] = PullStatus.CLONE_REQUIRED_NO_URL.value
        result["success"] = False
        result["errors"].append("仓库不存在且未提供 REPO_URL，无法克隆")
        result["perm"] = {
            "readonly_before_pull": dir_existed,
            "restored_after_pull": dir_existed,
            "note": "目录不存在/未克隆，未设置只读",
        }
        _dump(result, out_json)
        return result

    # ===== 写仓库操作：临时放开只读，退出时恢复 =====
    with _readonly_guard(local):
        # 阶段1：确保仓库存在
        if state != _STATE_REPO:
            if not clone(url, local, errors):
                result["status"] = PullStatus.CLONE_FAILED.value
                result["success"] = False
                result["perm"] = {
                    "readonly_before_pull": dir_existed,
                    "restored_after_pull": False,
                    "note": "克隆失败，目录可能已清理，未强制恢复只读",
                }
                _dump(result, out_json)
                return result
            online = False
        else:
            if not url:
                url = get_remote_url(local)
                result["url"] = _mask_url(url)

        # 阶段2~4：双 ref 模式有意义；WORKTREE 模式跳过
        worktree = _is_worktree_mode(target)
        result["mode"] = PullMode.WORKTREE.value if worktree else PullMode.DUAL_REF.value
        if not worktree:
            result["shallow"] = is_shallow(local)
            result["fetch_status"] = fetch_and_deepen(local, [base, target], deepen, errors, online)
            if result["shallow"]:
                result["shallow"] = is_shallow(local)
                result["deepened"] = (
                    result["fetch_status"]
                    in (FetchStatus.FETCHED.value, FetchStatus.DEEPEN_FAILED.value)
                    and not result["shallow"]
                )
            ensure_refs(local, [base, target], errors, online)
            result["checked_out"] = checkout(local, target, errors)
        else:
            result["fetch_status"] = FetchStatus.WORKTREE.value
            result["checked_out"] = "WORKTREE(分析当前工作树)"

        # 阶段5：变更文件集合
        result["base_sha"] = sha(local, base)
        if worktree:
            cf = changed_vs_worktree(local, base)
            result["target"] = "WORKTREE"
        else:
            result["target_sha"] = sha(local, target)
            cf = changed_files(local, base, target)
        result["changed_count"] = len(cf)
        result["changed_files"] = cf

    # 状态收敛
    if any("ref_unavailable" in e for e in errors):
        result["status"] = PullStatus.REFS_UNAVAILABLE.value
        result["success"] = False
    elif result["fetch_status"] == FetchStatus.SKIPPED_OFFLINE.value:
        result["status"] = PullStatus.OK_OFFLINE.value
    else:
        result["status"] = PullStatus.OK.value

    result["perm"] = {
        "readonly_before_pull": dir_existed,
        "restored_after_pull": True,
        "note": "拉取前已置只读；写仓库操作期间临时读写；拉取完成已恢复只读",
    }
    _dump(result, out_json)
    return result


def _dump(result: dict, out_json: str) -> None:
    if out_json:
        try:
            Path(out_json).parent.mkdir(parents=True, exist_ok=True)
            Path(out_json).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
    printable = {k: v for k, v in result.items() if k != "changed_files"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    if result["changed_files"]:
        print(f"[changed_files] 共 {len(result['changed_files'])} 个（前 10）：")
        for p in result["changed_files"][:10]:
            print("  -", p)


def main() -> int:
    ap = argparse.ArgumentParser(description="拉取代码（qa-code-pull）独立模块")
    ap.add_argument(
        "--url",
        default=os.environ.get("REPO_URL", ""),
        help="git 仓库地址（仅克隆时需要；已存在仓库自动读 remote）",
    )
    ap.add_argument(
        "--path", default=os.environ.get("LOCAL_PATH", DEFAULT_LOCAL), help="本地仓库路径"
    )
    ap.add_argument(
        "--base",
        default=os.environ.get("DIFF_BASE", DEFAULT_BASE),
        help="diff 基线 ref（默认 HEAD，配合 --target WORKTREE 走就地基线模式）",
    )
    ap.add_argument(
        "--target",
        default=os.environ.get("DIFF_TARGET", DEFAULT_TARGET),
        help="diff 目标 ref（默认 WORKTREE：分析当前工作树）",
    )
    ap.add_argument(
        "--deepen",
        type=int,
        default=int(os.environ.get("DEEPEN", DEFAULT_DEEPEN)),
        help="浅克隆加深深度",
    )
    ap.add_argument(
        "--out",
        default=os.environ.get("PULL_RESULT_JSON", ""),
        help="结果 JSON 输出路径（默认写到 LOCAL_PATH 同级 .pull_result.json）",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="当 success=False 时以非零退出码终止（默认恒 0，保证调用方无报错）",
    )
    args = ap.parse_args()

    out_json = args.out or str(Path(args.path).resolve().parent / ".pull_result.json")
    result = pull(args.url, args.path, args.base, args.target, args.deepen, out_json)
    # 默认退出码恒 0；--strict 下严重错误非零退出
    sys.exit(1 if (args.strict and not result.get("success")) else 0)


if __name__ == "__main__":
    raise SystemExit(main())
