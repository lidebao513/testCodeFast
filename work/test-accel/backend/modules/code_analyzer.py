"""代码分析器：以"读代码结构"(AST/正则)为主，提取功能点。
- api：后端接口声明（FastAPI/Flask 路由装饰器）
- page：前端路由（vue-router / react-router 的 path 定义）
- component：关键交互组件（.vue / 含交互钩子的组件文件，启发式）
LLM 仅作可选增强（llm_client.enhance），关闭时纯结构结果。
提取稳定、可复现，不依赖 LLM；符合用户拍板"功能点提取=读代码结构"。

三个入口：
- analyze(local_path)                全量扫描（原行为，等价于遍历全部代码文件）
- analyze_files(local_path, files)   只分析指定文件列表（增量对比：新版本侧）
- analyze_text(rel, text)            分析单段文本（增量对比：历史版本侧，内容来自 git show）
"""
import re
import subprocess
from pathlib import Path

# 跳过这些目录/文件，避免噪声与耗时
_SKIP_DIRS = ("node_modules", ".git", "venv", "dist", "build", "__pycache__",
              "audithandover", "audit_handover", "audit_safeguard")
_MAX_FILE = 300_000  # 超过 300KB 的文件跳过

# 关注的代码文件扩展名
_CODE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".vue")
# rglob 用的 glob 模式（与 _CODE_EXTS 一一对应）
_GLOB_PATTERNS = ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.vue")

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
    # ================= 底层扫描：单段文本 → 功能点 =================

    def _scan_api(self, rel: str, text: str):
        """后端接口（仅 .py）"""
        if not rel.lower().endswith(".py"):
            return []
        out = []
        for m in _PY_ROUTE_RE.finditer(text):
            method, path = m.group(1).upper(), m.group(2)
            out.append({
                "file_path": rel,
                "name": f"{method} {path}",
                "description": f"后端接口 {method} {path}",
                "ftype": "api",
            })
        return out

    def _scan_page(self, rel: str, text: str):
        """前端页面/路由：仅扫描路由相关文件，避免把任意 path: 字符串误当路由"""
        low = rel.lower()
        if "router" not in low and "route" not in low:
            return []
        out = []
        for m in _ROUTE_PATH_RE.finditer(text):
            p = m.group(1)
            if p in ("/", "*") or p.startswith(":") or p.startswith("$"):
                continue
            # 跳过明显非路由的 path（如文件路径常量）
            if any(seg in p for seg in (".", "node_modules", "/src/", "assets")):
                continue
            out.append({
                "file_path": rel,
                "name": f"页面路由 {p}",
                "description": f"前端页面/路由 {p}",
                "ftype": "page",
            })
        return out

    def _scan_component(self, rel: str, text: str, project_type: str = "pc"):
        """关键交互组件（启发式：含按钮/表单/上传等交互钩子）"""
        if project_type not in ("pc", "h5"):
            return []
        if not rel.lower().endswith(".vue"):
            return []
        if _VUE_RE.search(text) and re.search(
                r"(@click|v-on|el-button|button|input|upload|form)", text, re.I):
            return [{
                "file_path": rel,
                "name": f"交互组件 {Path(rel).name}",
                "description": f"含交互钩子的组件 {rel}",
                "ftype": "component",
            }]
        return []

    def analyze_text(self, rel: str, text: str, project_type: str = "pc"):
        """分析单段文本 → 功能点列表。

        rel 为相对路径（决定扩展名判断与 router 启发式）；
        text 可以来自工作区文件，也可以来自 git show 取到的历史版本。
        """
        if not str(rel).lower().endswith(_CODE_EXTS):
            return []
        fps = []
        fps += self._scan_api(rel, text)
        if not str(rel).lower().endswith(".py"):
            fps += self._scan_page(rel, text)
            fps += self._scan_component(rel, text, project_type)
        return fps

    def analyze_content_map(self, content_map, project_type: str = "pc"):
        """批量分析 {rel_path: text} → 功能点列表（历史版本侧用）。"""
        fps = []
        for rel, text in content_map.items():
            if text is None:
                continue
            fps += self.analyze_text(rel, text, project_type)
        return self._dedup(fps)

    @staticmethod
    def _dedup(fps):
        """去重（同一文件同名只留一个）"""
        seen, uniq = set(), []
        for fp in fps:
            key = (fp["ftype"], fp["file_path"], fp["name"])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(fp)
        return uniq

    # ================= 文件遍历 =================

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

    # ================= 对外入口 =================

    def analyze(self, local_path: str, project_type: str = "pc"):
        """全量扫描（原行为）"""
        root = Path(local_path)
        if not root.exists():
            return []
        fps = []
        for f, rel in self._iter_code(root, _GLOB_PATTERNS):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            fps += self.analyze_text(rel, text, project_type)
        return self._dedup(fps)

    def analyze_files(self, local_path: str, file_paths, project_type: str = "pc"):
        """只分析指定的文件列表（相对路径），用于增量对比的新版本侧。

        自动跳过：非代码扩展名、不存在、目录、超过 _MAX_FILE 的文件。
        """
        root = Path(local_path)
        if not root.exists():
            return []
        fps = []
        for rel in file_paths:
            if not str(rel).lower().endswith(_CODE_EXTS):
                continue
            f = root / rel
            try:
                if not f.exists() or f.is_dir():
                    continue
                if f.stat().st_size > _MAX_FILE:
                    continue
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            fps += self.analyze_text(rel, text, project_type)
        return self._dedup(fps)


# ===================== 增强：全面测试点生成（v2） =====================
# 目标：不再只产出"路由是否存在"的浅探针，而是按完整代码派生
# 覆盖更充分的测试点：①API 路由按 path 归入业务模块；②每条路由展开
# 正常/鉴权/参数边界/资源不存在 四维；③抽取核心业务模块函数；
# ④前端页面可达 + 组件交互。全部可复现，不依赖 LLM。

# 模块归类规则（按 API path 命中关键词，顺序优先；re.search 故可命中任意位置）
_MODULE_RULES = [
    ("对话/会话 Chat", (r"/api/v1/chat", r"/chat-stream", r"/chat-resume",
                         r"/live-messages", r"/diag-log", r"/chat", r"/ask-context",
                         r"/ask-quota", r"/cancel", r"/summarize")),
    ("线程 Thread", (r"/threads", r"schedule")),
    ("产物/文档 Artifact", (r"/artifact", r"/artifacts", r"/docx-preview",
                            r"/xlsx-preview", r"/pptx-preview", r"/onlyoffice",
                            r"/documents", r"/document", r"/document_info", r"/wps", r"/dl")),
    ("记忆 Memory", (r"/memories",)),
    ("技能 Skill", (r"/skills", r"/my-skills")),
    ("智能体 Agent", (r"/agents",)),
    ("工具/集成 Tool", (r"/tools", r"/mcp-servers", r"/hook")),
    ("项目 Project", (r"/projects",)),
    ("日程 Schedule", (r"/schedule",)),
    ("通知 Notification", (r"/notifications",)),
    ("简报 Briefing", (r"/briefing", r"/today")),
    ("执行大厅 ExecHall", (r"/exec-hall",)),
    ("分享 Share", (r"/share",)),
    ("上传 Upload", (r"/uploads",)),
    ("ASR 语音", (r"/asr",)),
    ("贡献 Contribution", (r"/contributions",)),
    ("运维 Ops", (r"/ops",)),
    ("审计/审核看板 Audit", (r"/api/audit", r"/audit", r"/regulations", r"/catalog",
                             r"/logs", r"/mock", r"/status", r"/items", r"/pending")),
    ("SQL/查询 Query", (r"/api/sql", r"/sql_explanation")),
    ("账户/用户/鉴权 Auth", (r"/login", r"/accounts", r"auth", r"token", r"/renew",
                              r"/users", r"/roles", r"/me", r"/logout",
                              r"/change-password", r"/refresh", r"/gateway-user",
                              r"/gateway-renew", r"/unified-login")),
    ("健康/其它", (r"/health",)),
]

# 需要"资源不存在⇒404"维度的路由（含 {id}/{name}/{token} 等路径参数）
_ID_PARAM_RE = re.compile(r"\{[^}]+\}|<[^>]+>")

# 核心业务模块（抽取其中顶层函数/类作为业务级测试点，覆盖代码逻辑面）
_CORE_MODULES = [
    "server.py", "gateway_crypto.py", "unified_auth.py", "email_live.py",
    "briefing.py", "morning_brief.py", "summarizer.py", "notifications.py",
    "exec_hall_metrics.py", "exec_hall_perf.py", "pipeline_api.py",
    "gateway_middleware.py", "rq_client.py", "wps_office_api.py",
]


def _module_of(path: str) -> str:
    for name, pats in _MODULE_RULES:
        for p in pats:
            if re.search(p, path):
                return name
    return "未归类 Other"


# ===================== 标签：全量 / 更新 =====================
# 用途：区分「全量测试点」（完整回归集）与「本次拉取代码后，通过代码对比
# 识别出的变更测试点」。变更测试点 = 其底层 source 文件出现在 base..target
# 的 diff 变更文件集合中，打标签『更新』；其余打『全量』。

def compute_diff_changed_files(repo_path: str, base: str, target: str) -> set:
    """获取 base..target 的变更文件集合（相对仓库根的路径）。

    用于给测试点打『更新』标签：测试点的 source 命中此集合即视为本次变更测试点。
    git 不可用时返回空集（此时全部测试点标『全量』）。
    """
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "diff", "--name-only", base, target],
            capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return set()
        return {ln.strip() for ln in out.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def _is_changed(source: str, changed_set) -> bool:
    """判断测试点的 source 是否命中风云变更文件。

    source 可能是：
      - 完整相对路径（API/前端点，如 backend/research-agent-source/server.py）
      - 仅文件名（业务函数点，如 server.py）
    两种形态都做精确匹配 + basename 兜底匹配。
    """
    if not changed_set or not source:
        return False
    s = source.strip()
    if s in changed_set:
        return True
    base = s.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if not base:
        return False
    for c in changed_set:
        cb = c.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if cb == base:
            return True
    return False


class _ComprehensiveBuilder:
    """把 code_analyzer.analyze() 的基础功能点，扩成全面测试点。"""

    def build(self, local_path: str, project_type: str = "pc",
               changed_files=None, scopes=None) -> dict:
        base = code_analyzer.analyze(local_path, project_type)
        api_fps = [f for f in base if f["ftype"] == "api"]
        page_fps = [f for f in base if f["ftype"] == "page"]
        comp_fps = [f for f in base if f["ftype"] == "component"]

        raw = []
        # ① API 路由 → 四维展开
        for f in api_fps:
            name = f["name"]
            if " " in name:
                method, path = name.split(" ", 1)
            else:
                method, path = "GET", name
            module = _module_of(path)
            raw += self._expand_api(method, path, f["file_path"], module)
        # ② 核心业务模块函数
        raw += self._expand_business(local_path)
        # ③ 前端页面可达
        for f in page_fps:
            raw.append({
                "module": "前端 Frontend", "area": f["name"].replace("页面路由", "").strip(),
                "method": "PAGE", "tp_type": "正常",
                "name": f"页面可达 {f['name']}",
                "dimension": "页面/路由可达", "source": f["file_path"],
                "expect": "路由在 router 中定义且可导航加载，无白屏/404",
            })
        # ④ 组件交互
        for f in comp_fps:
            raw.append({
                "module": "前端 Frontend", "area": f["name"],
                "method": "UI", "tp_type": "正常",
                "name": f"交互组件 {f['name']}",
                "dimension": "交互元素可用", "source": f["file_path"],
                "expect": "组件含交互钩子(@click/按钮/表单/上传)，可正常触发",
            })

        # 范围过滤（Scope）：仅保留测试类型(tp_type)落在 scopes 内的测试点。
        # scopes=None 表示不过滤（兼容旧行为，生成全部四种类型）。
        # scopes 为空集合时结果为空（调用方 resolve_scope 不会返回空集）。
        if scopes is not None:
            raw = [r for r in raw if r["tp_type"] in scopes]

        # 标签：source 命中变更文件的测试点标『更新』，其余标『全量』
        for r in raw:
            r["tag"] = "更新" if _is_changed(r["source"], changed_files) else "全量"

        # 统一编号 + 模块汇总
        for i, r in enumerate(raw, 1):
            r["id"] = f"TP-{i:03d}"
        modules = {}
        for r in raw:
            m = r["module"]
            modules.setdefault(m, {"api": 0, "business": 0, "frontend": 0, "total": 0,
                                   "areas": set(), "updated": 0})
            modules[m]["total"] += 1
            modules[m]["areas"].add(r["area"])
            if r["method"] in ("GET", "POST", "PUT", "DELETE", "PATCH",
                               "OPTIONS", "HEAD"):
                modules[m]["api"] += 1
            elif r["method"] in ("PAGE", "UI"):
                modules[m]["frontend"] += 1
            else:
                modules[m]["business"] += 1
            if r["tag"] == "更新":
                modules[m]["updated"] += 1
        module_summary = []
        for m, v in modules.items():
            module_summary.append({
                "module": m, "total": v["total"], "api": v["api"],
                "business": v["business"], "frontend": v["frontend"],
                "updated": v["updated"],
                "area_count": len(v["areas"]),
                "areas": sorted(v["areas"])[:12],
            })
        module_summary.sort(key=lambda x: -x["total"])

        by_type = {}
        for r in raw:
            by_type[r["tp_type"]] = by_type.get(r["tp_type"], 0) + 1

        by_tag = {}
        for r in raw:
            by_tag[r["tag"]] = by_tag.get(r["tag"], 0) + 1

        return {
            "total": len(raw),
            "by_type": by_type,
            "by_tag": by_tag,
            "module_summary": module_summary,
            "test_points": raw,
        }

    def _expand_api(self, method, path, file_path, module):
        tps = [{
            "module": module, "area": path, "method": method,
            "tp_type": "正常",
            "name": f"接口 {method} {path} · 功能可用性",
            "dimension": "正常-可用性",
            "source": file_path,
            "expect": "路由存在且可调用，携带合法凭证返回预期结构(2xx)",
        }, {
            "module": module, "area": path, "method": method,
            "tp_type": "安全",
            "name": f"接口 {method} {path} · 鉴权校验",
            "dimension": "安全-鉴权缺失",
            "source": file_path,
            "expect": "缺失/错误 Authorization → 401/403，不泄露业务数据",
        }, {
            "module": module, "area": path, "method": method,
            "tp_type": "边界",
            "name": f"接口 {method} {path} · 参数校验",
            "dimension": "边界-参数缺失/非法",
            "source": file_path,
            "expect": "缺失必填参数 → 422/400；非法类型/越界值 → 400",
        }]
        if _ID_PARAM_RE.search(path):
            tps.append({
                "module": module, "area": path, "method": method,
                "tp_type": "异常",
                "name": f"接口 {method} {path} · 资源不存在",
                "dimension": "异常-资源不存在",
                "source": file_path,
                "expect": "访问不存在/非法的 {id} → 404，错误信息友好",
            })
        # 写操作补充越权维度
        if method in ("PUT", "PATCH", "DELETE") and _ID_PARAM_RE.search(path):
            tps.append({
                "module": module, "area": path, "method": method,
                "tp_type": "安全",
                "name": f"接口 {method} {path} · 越权访问",
                "dimension": "安全-越权",
                "source": file_path,
                "expect": "操作他人资源 → 403，不越权修改",
            })
        return tps

    def _expand_business(self, local_path: str):
        root = Path(local_path)
        # 核心模块可能在仓库根，也可能在 backend/research-agent-source 下
        candidates = [root, root / "backend" / "research-agent-source"]
        tps = []
        for mod in _CORE_MODULES:
            fp = None
            for c in candidates:
                p = c / mod
                if p.exists():
                    fp = p
                    break
            if fp is None:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            syms = re.findall(
                r"^(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\s*",
                text, re.M)
            # 去掉 dunder 与明显噪声，保留业务/接口/编排相关符号
            kept = [s for s in syms if not s.startswith("__")
                    and s not in ("def", "class")]
            # 每模块取前 12 个顶层符号作业务级覆盖点（保持可复现顺序）
            for s in kept[:12]:
                tps.append({
                    "module": f"业务函数·{mod}",
                    "area": s, "method": "FUNC",
                    "tp_type": "正常",
                    "name": f"{mod}::{s} 业务覆盖",
                    "dimension": "业务函数-逻辑可用",
                    "source": mod,
                    "expect": "函数/类可被调用且输入合法时输出符合预期（单测/集成覆盖）",
                })
        return tps


def generate_comprehensive_test_points(local_path: str, project_type: str = "pc",
                                        changed_files=None, scopes=None) -> dict:
    """独立入口：对完整代码生成全面测试点（v2）。

    changed_files: 可选，base..target 的变更文件集合（相对仓库根路径）。
        提供后会为每个测试点打『更新/全量』标签，便于筛选本次变更测试点。
    scopes: 可选，测试点范围集合，取值子集 {"正常","异常","安全","边界"}。
        - None        → 不过滤，生成全部四种类型（兼容旧行为）
        - {"正常"}     → 仅正常
        - {"正常","异常"} → 正常 + 异常（skill 默认范围）
        - {"安全","边界"} → 仅安全 + 边界
        过滤在「四维展开」之后、打标签/编号/汇总之前完成，使下游统计一致。
    """
    return _ComprehensiveBuilder().build(local_path, project_type, changed_files, scopes)


code_analyzer = CodeAnalyzer()
