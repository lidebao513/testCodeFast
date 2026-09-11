"""引擎 · 模块一：扫描（scan）。

职责单一：把仓库目录变成「可分析的文件集合」，并对每个文件**只读一次、只解析一次 AST**。
这是 legacy `code_analyzer.py` 中 `_SourceIndex` 想解决却被上帝模块淹没的那件事：
同文件被功能点提取、语义增强、测试点展开、hunk 打标反复读取，导致 O(n²) 级 IO。

对外只暴露两个东西：`SourceFile` 与 `Scanner`。
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


# 非业务目录：与业务无关，直接跳过
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset(
    {
        "venv",
        ".venv",
        "env",
        "node_modules",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        "site-packages",
    }
)

# 测试/脚手架文件名前缀：参与扫描但不作为「业务功能点」来源
NOISE_FILE_PREFIXES: tuple[str, ...] = ("test_", "conftest", "selftest_", "verify_")
NOISE_DIR_PARTS: tuple[str, ...] = ("tests", "test", "docs", "examples", "migrations")

# ---------------------------------------------------------------- 扩展名（单一真值）
# 前端类扩展名：**扫描器与 fp_extract 必须共用同一份**，否则会出现
# 「文件没被扫到 → 前端功能点恒为 0」的静默丢层（真实仓库上曾丢掉 147 个 .tsx）。
FRONTEND_EXTS: tuple[str, ...] = (".js", ".ts", ".tsx", ".jsx", ".vue")
# 全量扫描扩展名
SOURCE_EXTS: tuple[str, ...] = (".py", *FRONTEND_EXTS, ".html")


@dataclass
class SourceFile:
    """一个被扫描到的源码文件（AST 惰性解析、只解析一次）。"""

    rel: str  # 相对仓库根路径，**统一正斜杠**
    abspath: Path
    text: str
    _tree: ast.Module | None = field(default=None, repr=False)
    _parsed: bool = field(default=False, repr=False)

    @property
    def name(self) -> str:
        return self.rel.rsplit("/", 1)[-1]

    @property
    def ext(self) -> str:
        return self.abspath.suffix.lower()

    @property
    def is_python(self) -> bool:
        return self.ext == ".py"

    @property
    def is_noise(self) -> bool:
        parts = self.rel.split("/")
        if any(p in NOISE_DIR_PARTS for p in parts[:-1]):
            return True
        return self.name.startswith(NOISE_FILE_PREFIXES)

    def tree(self) -> ast.Module | None:
        """解析 AST（失败返回 None，并缓存结果避免重复解析）。"""
        if self._parsed:
            return self._tree
        self._parsed = True
        try:
            self._tree = ast.parse(self.text)
        except (SyntaxError, ValueError):
            self._tree = None
        return self._tree


class Scanner:
    """目录扫描器：产出 `SourceFile`，并按相对路径建索引。"""

    def __init__(
        self,
        root: str | Path,
        *,
        exts: tuple[str, ...] = SOURCE_EXTS,
        exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS,
        max_bytes: int = 2_000_000,
    ) -> None:
        self.root = Path(root).resolve()
        self.exts = exts
        self.exclude_dirs = exclude_dirs
        self.max_bytes = max_bytes

    def iter_files(self) -> Iterator[SourceFile]:
        """按稳定顺序产出文件（排序保证跨运行结果一致）。"""
        if not self.root.is_dir():
            return
        paths: list[Path] = []
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in self.exts:
                continue
            if any(seg in self.exclude_dirs for seg in p.parts):
                continue
            try:
                if p.stat().st_size > self.max_bytes:
                    continue
            except OSError:
                continue
            paths.append(p)

        for p in sorted(paths, key=lambda x: x.as_posix()):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            yield SourceFile(rel=self.rel_of(p), abspath=p, text=text)

    def rel_of(self, path: Path) -> str:
        """转成相对仓库根的正斜杠路径（与 git diff 路径形态一致）。"""
        try:
            rel = path.resolve().relative_to(self.root)
        except ValueError:
            rel = Path(path.name)
        return rel.as_posix()

    def index(self) -> dict[str, SourceFile]:
        """一次性建索引：{相对路径: SourceFile}。"""
        return {sf.rel: sf for sf in self.iter_files()}

    def list_records(self) -> list[dict[str, object]]:
        """轻量清单（供 API 输出，不携带全文）。"""
        return [
            {
                "path": sf.rel,
                "name": sf.name,
                "ext": sf.ext,
                "noise": sf.is_noise,
                "bytes": len(sf.text.encode("utf-8")),
            }
            for sf in self.iter_files()
        ]
