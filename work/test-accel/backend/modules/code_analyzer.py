"""代码分析器：以"读代码结构"(AST/正则)为主，提取功能点。
- api：后端接口声明（FastAPI/Flask 路由装饰器）
- page：前端路由（vue-router / react-router 的 path 定义）
- component：关键交互组件（.vue / 含交互钩子的组件文件，启发式）
LLM 仅作可选增强（llm_client.enhance），关闭时纯结构结果。
提取稳定、可复现，不依赖 LLM；符合用户拍板"功能点提取=读代码结构"。
"""
import re
from pathlib import Path

# 跳过这些目录/文件，避免噪声与耗时
_SKIP_DIRS = ("node_modules", ".git", "venv", "dist", "build", "__pycache__",
              "audithandover", "audit_handover", "audit_safeguard")
_MAX_FILE = 300_000  # 超过 300KB 的文件跳过

# 后端接口装饰器：@app.get("/x") / @router.post("/y")
_PY_ROUTE_RE = re.compile(
    r"""(?:app|router|bp|blueprint)\s*\.\s*(get|post|put|delete|patch|options|head)\s*\(\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
# 前端路由 path 定义
_ROUTE_PATH_RE = re.compile(r"""path\s*:\s*["']([^"']+)["']""")
# 组件文件识别（简单启发式）
_VUE_RE = re.compile(r"<(script|template)", re.IGNORECASE)


class CodeAnalyzer:
    def _iter_code(self, root: Path, patterns):
        for pat in patterns:
            for f in root.rglob(pat):
                rel = str(f.relative_to(root))
                lowered = rel.lower()
                if any(s in lowered for s in _SKIP_DIRS):
                    continue
                if f.stat().st_size > _MAX_FILE:
                    continue
                yield f, rel

    def analyze(self, local_path: str, project_type: str = "pc"):
        root = Path(local_path)
        if not root.exists():
            return []
        fps = []

        # ---- 后端接口 (api) ----
        for f, rel in self._iter_code(root, ("*.py",)):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in _PY_ROUTE_RE.finditer(text):
                method, path = m.group(1).upper(), m.group(2)
                if path.startswith("{") or path in ("/",):
                    # 跳过纯根或参数化过头的路由
                    pass
                fps.append({
                    "file_path": rel,
                    "name": f"{method} {path}",
                    "description": f"后端接口 {method} {path}",
                    "ftype": "api",
                })

        # ---- 前端页面/路由 (page) ----
        # 仅扫描路由相关文件，避免把任意 path: 字符串误当路由
        for f, rel in self._iter_code(root, ("*.ts", "*.tsx", "*.js", "*.jsx", "*.vue")):
            if "router" not in rel.lower() and "route" not in rel.lower():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in _ROUTE_PATH_RE.finditer(text):
                p = m.group(1)
                if p in ("/", "*") or p.startswith(":") or p.startswith("$"):
                    continue
                # 跳过明显非路由的 path（如文件路径常量）
                if any(seg in p for seg in (".", "node_modules", "/src/", "assets")):
                    continue
                fps.append({
                    "file_path": rel,
                    "name": f"页面路由 {p}",
                    "description": f"前端页面/路由 {p}",
                    "ftype": "page",
                })

        # ---- 关键交互组件 (component) —— 启发式：含按钮/表单/上传等交互钩子 ----
        if project_type in ("pc", "h5"):
            for f, rel in self._iter_code(root, ("*.vue",)):
                try:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if _VUE_RE.search(text) and re.search(r"(@click|v-on|el-button|button|input|upload|form)", text, re.I):
                    name = f.name
                    fps.append({
                        "file_path": rel,
                        "name": f"交互组件 {name}",
                        "description": f"含交互钩子的组件 {rel}",
                        "ftype": "component",
                    })

        # 去重（同一文件同名只留一个）
        seen, uniq = set(), []
        for fp in fps:
            key = (fp["ftype"], fp["file_path"], fp["name"])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(fp)
        return uniq


code_analyzer = CodeAnalyzer()
