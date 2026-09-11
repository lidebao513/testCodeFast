"""一次性迁移脚本：把核心生产文件里的裸枚举字面量替换为 backend.core.enums 引用。

只处理核心文件（排除 selftest_*/verify_* 历史脚手架、enums.py 自身、本脚本）。
- 自动确保 `from backend.core.enums import (...)` 存在（单行长形式，覆盖全部所需类）。
- 逐行剥离「行尾注释」后再做 token 替换，避免误改注释里的字面量。
- 跳过：接口 / 范围关键词(全部/所有/完整/all/ALL) / 通用摘要键(ok)。
- UI/PAGE/FUNC 一律映射 MethodMarker.*（当前代码库里它们只作 method 标记）。

用法：python scripts/migrate_enums.py   （幂等，可重跑）
"""

import os
import re


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = [
    "backend/main.py",
    "backend/modules/analytics.py",
    "backend/modules/case_generator.py",
    "backend/modules/code_analyzer.py",
    "backend/modules/executor.py",
]

# token -> (EnumClass, MEMBER)
REPL = {
    "正常": ("TPType", "NORMAL"),
    "异常": ("TPType", "ABNORMAL"),
    "安全": ("TPType", "SECURITY"),
    "边界": ("TPType", "BOUNDARY"),
    "全量": ("Tag", "FULL"),
    "更新": ("Tag", "UPDATE"),
    "api": ("FType", "API"),
    "page": ("FType", "PAGE"),
    "ui": ("FType", "UI"),
    "business": ("FType", "BUSINESS"),
    "component": ("FType", "COMPONENT"),
    "PAGE": ("MethodMarker", "PAGE"),
    "UI": ("MethodMarker", "UI"),
    "FUNC": ("MethodMarker", "FUNC"),
    "正常-可用性": ("Dimension", "AVAIL"),
    "安全-鉴权缺失": ("Dimension", "AUTH_MISS"),
    "安全-越权": ("Dimension", "PRIV_ESC"),
    "边界-参数缺失/非法": ("Dimension", "PARAM_ILLEGAL"),
    "异常-资源不存在": ("Dimension", "RES_NOT_FOUND"),
    "业务函数-逻辑可用": ("Dimension", "BIZ_LOGIC"),
    "页面/路由可达": ("Dimension", "PAGE_REACH"),
    "交互元素可用": ("Dimension", "INTERACTIVE"),
    "pass": ("ExecStatus", "PASS"),
    "fail": ("ExecStatus", "FAIL"),
    "error": ("ExecStatus", "ERROR"),
    "skipped": ("ExecStatus", "SKIPPED"),
    "structural_only": ("ExecStatus", "STRUCTURAL_ONLY"),
    "blocked_auth": ("ExecStatus", "BLOCKED_AUTH"),
    "blocked_review": ("ExecStatus", "BLOCKED_REVIEW"),
}
SKIP_TOKENS = {"接口", "全部", "所有", "完整", "all", "ALL"}

CANON_IMPORT = (
    "from backend.core.enums import (TPType, Tag, FType, VerifyLayer, Dimension, "
    "MethodMarker, ExecStatus, CaseLifecycleStatus, ReviewStatus, PullStatus, "
    "SCOPE_KEY_ALL, derive_verify_layer, method_kind, is_http_method, KIND_DISPLAY)  "
    "# noqa: E402  单一枚举真值源"
)

_token_re = re.compile(r'([\'"])((?:\\.|[^\\\'"])+)(\1)')


def split_comment(line: str):
    """返回 (代码部分, 注释部分)；注释指不在引号内的首个 #。"""
    in_s = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            if in_s is None:
                in_s = ch
            elif in_s == ch:
                in_s = None
        elif ch == "#" and in_s is None:
            return line[:i], line[i:]
    return line, ""


def repl_code(code: str) -> str:
    def sub(m):
        tok = m.group(2)
        if tok in SKIP_TOKENS or tok not in REPL:
            return m.group(0)
        cls, mem = REPL[tok]
        return f"{cls}.{mem}.value"

    return _token_re.sub(sub, code)


def ensure_import(lines):
    """确保存在 backend.core.enums 的 import，返回新行列表。"""
    for idx, ln in enumerate(lines):
        if "from backend.core.enums import" in ln:
            # 找到该 import 块结束位置
            if "(" in ln:
                end = idx
                while ")" not in lines[end]:
                    end += 1
                block = list(range(idx, end + 1))
            else:
                block = [idx]
            new = list(lines)
            for b in reversed(block):
                new.pop(b)
            new.insert(idx, CANON_IMPORT)
            return new
    # 不存在：插到第一个 import/from 之后（或文件头）
    new = list(lines)
    insert_at = 0
    for i, ln in enumerate(lines):
        if ln.startswith(("import ", "from ")):
            insert_at = i + 1
            break
    new.insert(insert_at, CANON_IMPORT)
    return new


def migrate_file(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        print(f"[skip] 不存在: {rel}")
        return
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    changed = 0
    for ln in lines:
        code, comment = split_comment(ln)
        new_code = repl_code(code)
        if new_code != code:
            changed += 1
        out.append(new_code + (comment if comment else ""))
    out = ensure_import(out)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"[ok] {rel}: 替换 {changed} 行, 已确保枚举 import")


if __name__ == "__main__":
    for f in CORE:
        migrate_file(f)
    print("迁移完成。请运行 scripts/check_enums.py 核验。")
