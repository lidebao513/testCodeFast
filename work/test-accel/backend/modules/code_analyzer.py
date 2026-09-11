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

阶段2 增强（统一契约 C1 / 功能点业务语义 A1 / 双向追溯 A2）：
- C1：功能点与测试点共用同一套 **统一数据契约**（fp_id / semantic / module / action /
  impl / loc），并共用 **单次扫描索引 `_SourceIndex`**（同文件只读一次、只解析一次 AST）。
- A1：功能点除机器可读的 name 外，补出业务域(module)、业务动作(action)、
  业务语义(semantic)、实现函数与 docstring(impl)、源码位置(loc) 与业务化 title/description。
- A2：每条测试点携带来源功能点 fp_id，功能点侧可反查其派生的全部测试点，
  形成 **功能点 ↔ 测试点 双向追溯**（输出 fp_index / traceability）。
"""

import ast
import hashlib
import re
import subprocess
from pathlib import Path

from backend.core.enums import (
    Dimension,
    FType,
    MethodMarker,
    Tag,
    TPType,
    derive_verify_layer,
    method_kind,
)


# 跳过这些目录/文件，避免噪声与耗时
_SKIP_DIRS = (
    "node_modules",
    ".git",
    "venv",
    "dist",
    "build",
    "__pycache__",
    "audithandover",
    "audit_handover",
    "audit_safeguard",
)
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

# 测试点来源种类（kind）：用于「接口」范围按来源筛选已有测试点
_HTTP_VERBS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")


class ScopeSpec:
    """测试点范围描述符。

    - tp_types: 行为维度集合（正常/异常/安全/边界，见 TPType）；空集合理论上不会由 resolve_scope 产生。
    - kinds: 来源种类过滤；None 表示不限来源。注意：「接口」**不是**范围关键词
      （历史上曾用作来源筛选），现改为独立执行层枚举 VerifyLayer；接口来源筛选可由
      verify_layer=接口（=ftype∈{api,business}）等价覆盖。此处 kinds 仅作通用来源过滤保留。
    """

    __slots__ = ("kinds", "tp_types")

    def __init__(self, tp_types, kinds=None):
        self.tp_types = tp_types
        self.kinds = kinds

    def __repr__(self):
        return f"ScopeSpec(tp_types={self.tp_types}, kinds={self.kinds})"


def _kind_of(r: dict) -> str:
    """由测试点的 method 推导来源种类：api / page / ui / business。

    取 method 首 token 判定（兼容「GET」或「GET /path」两种写法）。统一委托 enums.method_kind。
    """
    return method_kind(r.get("method"))


class CodeAnalyzer:
    # ================= 底层扫描：单段文本 → 功能点 =================

    def _scan_api(self, rel: str, text: str):
        """后端接口（仅 .py）"""
        if not rel.lower().endswith(".py"):
            return []
        out = []
        for m in _PY_ROUTE_RE.finditer(text):
            method, path = m.group(1).upper(), m.group(2)
            out.append(
                {
                    "file_path": rel,
                    "name": f"{method} {path}",
                    "description": f"后端接口 {method} {path}",
                    "ftype": FType.API.value,
                    # 统一契约（C1）：结构化字段，供下游免字符串解析直接使用
                    "method": method,
                    "path": path,
                }
            )
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
            out.append(
                {
                    "file_path": rel,
                    "name": f"页面路由 {p}",
                    "description": f"前端页面/路由 {p}",
                    "ftype": FType.PAGE.value,
                    "route": p,  # 统一契约（C1）
                }
            )
        return out

    def _scan_component(self, rel: str, text: str, project_type: str = "pc"):
        """关键交互组件（启发式：含按钮/表单/上传等交互钩子）"""
        if project_type not in ("pc", "h5"):
            return []
        if not rel.lower().endswith(".vue"):
            return []
        if _VUE_RE.search(text) and re.search(
            r"(@click|v-on|el-button|button|input|upload|form)", text, re.I
        ):
            return [
                {
                    "file_path": rel,
                    "name": f"交互组件 {Path(rel).name}",
                    "description": f"含交互钩子的组件 {rel}",
                    "ftype": FType.COMPONENT.value,
                }
            ]
        return []

    def analyze_text(self, rel: str, text: str, project_type: str = "pc", index=None):
        """分析单段文本 → 功能点列表（含 A1 业务语义）。

        rel 为相对路径（决定扩展名判断与 router 启发式）；
        text 可以来自工作区文件，也可以来自 git show 取到的历史版本。
        index 为可选的 `_SourceIndex`（C1 去重扫描）：传入时复用其符号表，
        不传则就地解析该段文本（diff_analyzer 的历史版本场景）。
        """
        if not str(rel).lower().endswith(_CODE_EXTS):
            return []
        fps = []
        fps += self._scan_api(rel, text)
        if not str(rel).lower().endswith(".py"):
            fps += self._scan_page(rel, text)
            fps += self._scan_component(rel, text, project_type)
        return _enrich_fps(fps, rel, text, index)

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
                # 统一为正斜杠：与 git diff 输出的路径形态一致，
                # 避免 Windows 反斜杠导致的路径匹配失败（仅靠 basename 兜底不可靠）。
                rel = str(f.relative_to(root)).replace("\\", "/")
                lowered = rel.lower()
                if any(s in lowered for s in _SKIP_DIRS):
                    continue
                if f.stat().st_size > _MAX_FILE:
                    continue
                yield f, rel

    # ================= 对外入口 =================

    def analyze(self, local_path: str, project_type: str = "pc", index=None):
        """全量扫描（原行为）。

        index 为 `_SourceIndex`（C1）：传入时功能点提取与测试点派生共用同一次
        文件读取与 AST 解析，避免重复扫描整个仓库。
        """
        root = Path(local_path)
        if not root.exists():
            return []
        fps = []
        for f, rel in self._iter_code(root, _GLOB_PATTERNS):
            try:
                text = (
                    index.text(rel)
                    if index is not None
                    else f.read_text(encoding="utf-8", errors="ignore")
                )
            except Exception:
                continue
            if not text:
                continue
            fps += self.analyze_text(rel, text, project_type, index)
        return self._dedup(fps)

    def analyze_files(self, local_path: str, file_paths, project_type: str = "pc", index=None):
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
                text = (
                    index.text(rel)
                    if index is not None
                    else f.read_text(encoding="utf-8", errors="ignore")
                )
            except Exception:
                continue
            fps += self.analyze_text(rel, text, project_type, index)
        return self._dedup(fps)


# ===================== 增强：全面测试点生成（v2） =====================
# 目标：不再只产出"路由是否存在"的浅探针，而是按完整代码派生
# 覆盖更充分的测试点：①API 路由按 path 归入业务模块；②每条路由展开
# 正常/鉴权/参数边界/资源不存在 四维；③抽取核心业务模块函数；
# ④前端页面可达 + 组件交互。全部可复现，不依赖 LLM。

# 模块归类规则（按 API path 命中关键词，顺序优先；re.search 故可命中任意位置）
_MODULE_RULES = [
    (
        "对话/会话 Chat",
        (
            r"/api/v1/chat",
            r"/chat-stream",
            r"/chat-resume",
            r"/live-messages",
            r"/diag-log",
            r"/chat",
            r"/ask-context",
            r"/ask-quota",
            r"/cancel",
            r"/summarize",
        ),
    ),
    ("线程 Thread", (r"/threads", r"schedule")),
    (
        "产物/文档 Artifact",
        (
            r"/artifact",
            r"/artifacts",
            r"/docx-preview",
            r"/xlsx-preview",
            r"/pptx-preview",
            r"/onlyoffice",
            r"/documents",
            r"/document",
            r"/document_info",
            r"/wps",
            r"/dl",
        ),
    ),
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
    (
        "审计/审核看板 Audit",
        (
            r"/api/audit",
            r"/audit",
            r"/regulations",
            r"/catalog",
            r"/logs",
            r"/mock",
            r"/status",
            r"/items",
            r"/pending",
        ),
    ),
    ("SQL/查询 Query", (r"/api/sql", r"/sql_explanation")),
    (
        "账户/用户/鉴权 Auth",
        (
            r"/login",
            r"/accounts",
            r"auth",
            r"token",
            r"/renew",
            r"/users",
            r"/roles",
            r"/me",
            r"/logout",
            r"/change-password",
            r"/refresh",
            r"/gateway-user",
            r"/gateway-renew",
            r"/unified-login",
        ),
    ),
    ("健康/其它", (r"/health",)),
]

# 需要"资源不存在⇒404"维度的路由（含 {id}/{name}/{token} 等路径参数）
_ID_PARAM_RE = re.compile(r"\{[^}]+\}|<[^>]+>")

# 业务模块发现：显式清单（优先命中，保留人工业务域映射）+ 动态发现（补足）
# 背景：原先只有硬编码 _CORE_MODULES + 固定候选目录，被测仓库后端重构成 tools/** 后
# 命中率为 0，business 功能点与 FUNC 测试点整体缺失（业务函数维度空转）。
# 现改为：显式清单命中即用；不足 _BUSINESS_MAX_MODULES 时按「业务密度」自动发现补足。
_CORE_MODULES = [
    "server.py",
    "gateway_crypto.py",
    "unified_auth.py",
    "email_live.py",
    "briefing.py",
    "morning_brief.py",
    "summarizer.py",
    "notifications.py",
    "exec_hall_metrics.py",
    "exec_hall_perf.py",
    "pipeline_api.py",
    "gateway_middleware.py",
    "rq_client.py",
    "wps_office_api.py",
]

# 显式清单的候选目录（随被测仓库结构调整；tools/ 为重构后的后端主目录）
_CORE_MODULE_DIRS = (
    "",  # 仓库根
    "backend/research-agent-source",
    "backend/research-agent-source/tools",
    "tools",
    "src",
)

# 动态发现参数（与历史「14 个核心模块 × 12 函数」同量级，避免测试点数量爆炸）
_BUSINESS_MAX_MODULES = 12  # 最多取多少个业务模块
_BUSINESS_MAX_SYMBOLS = 12  # 每模块最多取多少个顶层符号
_BUSINESS_MIN_SYMBOLS = 3  # 顶层符号少于此数的文件视为非业务模块
_BUSINESS_SCAN_LIMIT = 600  # 最多解析多少个 .py 做候选评估（性能保护）

# 噪声文件/目录：测试、迁移、脚手架、包声明等不参与业务模块评估
_NOISE_SEGMENTS = (
    "tests",
    "test",
    "__pycache__",
    "migrations",
    "scripts",
    "alembic",
    "docs",
    "examples",
    "demo",
    "fixtures",
    "regression",
    "benchmark",
    "mock",
    "seed",
    "workspace",
    "vendor",
    "third_party",
    "tmp",
    "temp",
)
_NOISE_BASENAMES = ("__init__.py", "conftest.py", "setup.py", "manage.py")

# 路径关键词 → 中文业务域（动态发现模块的业务域命名依据；**顺序优先**，具体规则在前）
# 注意：只匹配末两三段，且先做 models/schema 特判，避免 "models.py" 命中 "model"、
# "wechat" 命中 "chat" 这类误判。
_BUSINESS_DOMAIN_RULES = [
    (r"audit|review|regulat|compliance|catalog", "审计/审核"),
    (r"wechat|wecom|notif|remind|subscribe", "通知推送"),
    (r"auth|login|rbac|user|account|password|token|permission", "账户/用户/鉴权"),
    (r"email|mail|smtp|imap", "邮件处理"),
    (r"brief|report|summar|digest|rollup|daily|morning", "简报/总结"),
    (r"mcp|tool_|toolbox|integration|plugin|skill", "工具/集成"),
    (r"memor|knowledge|rag|retriev|vector", "记忆/知识库"),
    (r"sql|query|metric|dashboard|stat|analy|data", "数据查询/指标"),
    (r"schedul|cron|job|task|worker|queue|celery|rq|sync", "调度/同步任务"),
    (r"artifact|docx|xlsx|pptx|document|wps|office|export", "产物/文档"),
    (r"gateway|crypto|middleware|proxy", "网关/中间件"),
    (r"upload|file|storage|oss|s3", "文件/存储"),
    (r"chat|agent|llm|prompt|conversation", "对话/智能体编排"),
]
# 数据模型/结构定义文件：业务语义弱，单独归类，避免被 "model" 规则误判成对话域
_MODEL_BASENAMES = (
    "models.py",
    "model.py",
    "schemas.py",
    "schema.py",
    "types.py",
    "entities.py",
    "dto.py",
)
# 回退命名时忽略的通用层级（取其上层目录作为业务域名）
_GENERIC_SEGMENTS = (
    "tools",
    "backend",
    "research-agent-source",
    "src",
    "app",
    "main",
    "core",
    "services",
    "service",
    "modules",
    "lib",
)


def _is_noise_py(rel: str) -> bool:
    """判断该 .py 是否属于噪声（测试/迁移/包声明等），不参与业务模块发现。"""
    low = rel.lower()
    segs = low.split("/")
    if any(s in _NOISE_SEGMENTS for s in segs[:-1]):
        return True
    b = segs[-1]
    return bool(b in _NOISE_BASENAMES or b.startswith("test_") or b.endswith("_test.py"))


def _biz_of_path(rel: str) -> str:
    """由文件路径推导业务域：先命中关键词词典，否则取有意义的末级目录名。

    **只取末两三段匹配**：仓库根常带有通用/误导性层级（如 `research-agent-source`
    含 "agent" 会让全仓都命中「对话/智能体编排」），全路径匹配会严重误判。
    """
    parts = rel.split("/")
    tail = "/".join(parts[-2:]) if len(parts) >= 2 else rel
    low = tail.lower()
    if parts[-1].lower() in _MODEL_BASENAMES:
        return "数据模型定义"
    for pat, name in _BUSINESS_DOMAIN_RULES:
        if re.search(pat, low):
            return name
    named = [p for p in parts[:-1] if p.lower() not in _GENERIC_SEGMENTS]
    if named:
        return named[-1]
    return Path(rel).stem or "业务逻辑"


def _top_symbols(syms: dict, public_only: bool = True) -> list:
    """取文件顶层符号，按行号排序 → [(lineno, name, meta)]。

    public_only=True 时排除 `_` 开头的私有/内部符号：业务功能点应面向
    「对外能力」，把 `_helper` 之类内部实现列为测试点会稀释业务语义。
    """
    items = [
        (v.get("sl", 0), k, v)
        for k, v in syms.items()
        if isinstance(k, str)
        and v.get("top")
        and not k.startswith("__")
        and k not in ("def", "class")
        and not (public_only and k.startswith("_"))
    ]
    items.sort(key=lambda x: (x[0], x[1]))
    return items


def _iter_py(root: Path):
    """遍历仓库内全部 .py（沿用 _SKIP_DIRS / _MAX_FILE 过滤）。"""
    for f in root.rglob("*.py"):
        rel = str(f.relative_to(root)).replace("\\", "/")
        if any(s in rel.lower() for s in _SKIP_DIRS):
            continue
        try:
            if f.stat().st_size > _MAX_FILE:
                continue
        except Exception:
            continue
        yield f, rel


def discover_business_modules(
    local_path: str, index: "_SourceIndex", limit: int = _BUSINESS_MAX_MODULES
) -> list:
    """发现业务模块：显式清单优先，不足时按「业务密度」动态补足。

    返回 [(rel, biz, [(lineno, name, meta), ...]), ...]，结果确定可复现
    （按 顶层符号数降序 → 路径升序 排序）。

    动态发现的筛选：
      - 排除噪声文件（tests / migrations / __init__ 等）；
      - 顶层符号数 ≥ _BUSINESS_MIN_SYMBOLS，避免把小工具脚本当业务模块；
      - **路由主导的文件跳过**（路由数×2 ≥ 顶层符号数）——这类文件已由 api 维度覆盖，
        再抽一遍会造成重复测试点。
    """
    root = Path(local_path)
    picks, seen = [], set()

    # ① 显式核心模块（保留人工业务域映射 _CORE_MODULE_BIZ）
    for mod in _CORE_MODULES:
        for d in _CORE_MODULE_DIRS:
            p = (root / d / mod) if d else (root / mod)
            if not p.exists():
                continue
            rel = str(p.relative_to(root)).replace("\\", "/")
            tops = _top_symbols(index.symbols(rel))
            if not tops:
                continue
            picks.append((rel, _CORE_MODULE_BIZ.get(mod, "业务逻辑"), tops))
            seen.add(rel)
            break
        if len(picks) >= limit:
            return picks[:limit]

    # ② 动态发现补足
    cands = []
    n = 0
    for _f, rel in _iter_py(root):
        if rel in seen or _is_noise_py(rel):
            continue
        n += 1
        if n > _BUSINESS_SCAN_LIMIT:
            break
        syms = index.symbols(rel)
        tops = _top_symbols(syms)
        if len(tops) < _BUSINESS_MIN_SYMBOLS:
            continue
        routes = [k for k in syms if isinstance(k, tuple)]
        if routes and len(routes) * 2 >= len(tops):
            continue  # 路由主导 → 已由 api 维度覆盖
        cands.append((len(tops), rel, tops))
    cands.sort(key=lambda x: (-x[0], x[1]))
    for _score, rel, tops in cands:
        if rel in seen:
            continue
        picks.append((rel, _biz_of_path(rel), tops))
        seen.add(rel)
        if len(picks) >= limit:
            break
    return picks


# ===================== 业务语义词典（B2） =====================
# 用于把「机械的接口/函数模板描述」升级为「带业务含义的测试点」，
# 使阶段3（用例生成）与阶段6（报告）能锚定真实业务场景。

# ① HTTP 方法 → 默认业务动作
_METHOD_ACTION = {
    "GET": "查询",
    "POST": "提交/创建",
    "PUT": Tag.UPDATE.value,
    "PATCH": "部分更新",
    "DELETE": "删除",
    "OPTIONS": "预检",
    "HEAD": "探活",
}

# ② 路径关键词 → 具体业务动作（优先于方法默认动作；顺序优先匹配）
_BIZ_PATH_RULES = [
    (r"stream", "流式输出"),
    (r"export|download|/dl", "导出下载"),
    (r"upload", "上传导入"),
    (r"import", "数据导入"),
    (r"search|query|retriev|sql", "检索查询"),
    (r"approv|audit|review|pending", "审批审核"),
    (r"cancel|abort|stop", "取消中止"),
    (r"login|logout|token|auth|password|renew", "登录鉴权"),
    (r"notif|remind|subscribe", "通知订阅"),
    (r"schedul|cron|sync", "调度同步"),
    (r"summar|brief|report", "总结简报"),
    (r"preview", "在线预览"),
    (r"share", "分享协作"),
    (r"artifact|docx|xlsx|pptx|document|wps", "产物文档"),
    (r"memor", "记忆管理"),
    (r"skill", "技能管理"),
    (r"agent", "智能体编排"),
    (r"thread", "会话线程"),
    (r"chat|ask|conversation", "对话交互"),
    (r"health|status|ping", "健康检查"),
]

# ③ 核心业务模块 → 业务域名称
_CORE_MODULE_BIZ = {
    "server.py": "主服务编排",
    "gateway_crypto.py": "网关加解密",
    "unified_auth.py": "统一身份鉴权",
    "email_live.py": "邮件实时处理",
    "briefing.py": "晨会简报",
    "morning_brief.py": "晨报生成",
    "summarizer.py": "内容总结",
    "notifications.py": "通知推送",
    "exec_hall_metrics.py": "执行大厅指标",
    "exec_hall_perf.py": "执行大厅性能",
    "pipeline_api.py": "流水线接口",
    "gateway_middleware.py": "网关中间件",
    "rq_client.py": "异步任务队列",
    "wps_office_api.py": "WPS 办公集成",
}


def _biz_label(module_label: str) -> str:
    """模块标签取中文业务名：'对话/会话 Chat' → '对话/会话'"""
    return (module_label or "").split(" ")[0] or "通用"


def _act_of(method: str, path: str) -> str:
    """由路径关键词（优先）+ HTTP 方法推导业务动作。"""
    low = (path or "").lower()
    for pat, act in _BIZ_PATH_RULES:
        if re.search(pat, low):
            return act
    return _METHOD_ACTION.get(method, "调用")


def _expect_for(
    tp_type: str, dimension: str, biz: str, act: str, method: str, path: str, impl: str = ""
) -> str:
    """按维度产出「带业务语义」的预期（替代原通用模板话术）。"""
    tail = f"；实现参考 {impl}" if impl else ""
    if dimension == Dimension.AUTH_MISS.value:
        return (
            f"{biz}·{act} 鉴权校验：缺失/错误 Authorization → 401/403，"
            f"不得返回任何{biz}业务数据{tail}"
        )
    if dimension == Dimension.PRIV_ESC.value:
        return f"{biz}·{act} 越权防护：操作他人资源 → 403，不产生越权修改{tail}"
    if dimension == Dimension.PARAM_ILLEGAL.value:
        return (
            f"{biz}·{act} 入参校验：缺失必填 / 类型错误 / 越界值 → 422/400，"
            f"错误信息可定位到具体字段{tail}"
        )
    if dimension == Dimension.RES_NOT_FOUND.value:
        return (
            f"{biz}·{act} 资源不存在：访问不存在或非法的 {{id}} → 404，"
            f"提示明确且不暴露内部细节{tail}"
        )
    return (
        f"{biz}·{act} 功能可用：{method} {path} 路由存在且可调用，"
        f"合法请求返回预期业务结果（2xx），关键字段完整{tail}"
    )


def _expect_func(biz: str, fname: str, doc: str = "") -> str:
    tail = f"；实现说明：{doc}" if doc else ""
    return f"{biz} 业务函数 {fname} 逻辑正确：合法输入输出符合预期，异常输入不崩溃且可观测{tail}"


def _expect_ui(kind: str, area: str) -> str:
    if kind == MethodMarker.PAGE.value:
        return f"前端页面 {area} 可导航加载：路由在 router 中定义，无白屏/404，关键区域正常渲染"
    return f"交互组件 {area} 可正常触发：含交互钩子(@click/表单/上传)，操作有响应"


def _module_of(path: str) -> str:
    for name, pats in _MODULE_RULES:
        for p in pats:
            if re.search(p, path):
                return name
    return "未归类 Other"


# ===================== 统一数据契约（C1） =====================
# 功能点(FP) 与 测试点(TP) 共用同一套字段语义，保证下游（阶段3用例/阶段6报告）
# 可以在两者之间自由跳转，而不是各自维护一套私有结构。
#
# 【FP 功能点契约】
#   fp_id       稳定唯一 ID（由 ftype|file_path|name 哈希得到，跨运行/跨机器稳定）
#   ftype       api / page / component / business
#   name        机器可读唯一名（如 "POST /chat"、"server.py::foo"）——保持不变，
#               兼容 DB 存储与 case_generator 的既有解析逻辑
#   title       业务化显示名（A1）
#   description 业务化描述（A1）
#   module      业务域（中文，如 "对话/会话"）
#   action      业务动作（如 "流式输出"）
#   semantic    "业务域 · 业务动作"
#   impl        实现函数 + docstring（真实业务语义来源）
#   loc         符号源码行区间 {"start","end"}（可空）
#   method/path/route  结构化字段（api/page 专有），供下游免解析使用
#
# 【TP 测试点契约】在既有字段之外新增：
#   fp_id / fp_name / fp_title  → 指向来源功能点（TP → FP 方向）
#   FP 侧 fp_index[fp_id]["test_points"] → 反向索引（FP → TP 方向）

FP_CONTRACT_VERSION = "1.0"


def fp_id_of(ftype: str, file_path: str, name: str) -> str:
    """稳定 ID：同一功能点在任何一次运行、任何一台机器上结果一致。

    用 md5(ftype|file_path|name) 前 8 位，避免路径中的中文/空格/分隔符影响，
    同时保证「代码没变 → ID 不变」，便于跨版本追溯与增量对比（对应 A6）。
    """
    key = f"{ftype}|{str(file_path).replace(chr(92), '/')}|{name}"
    return "FP-" + hashlib.md5(key.encode("utf-8")).hexdigest()[:8]  # nosec B324  # 非安全用途：仅生成稳定功能点 ID 指纹


def _fp_title(semantic: str, name: str) -> str:
    """业务化显示名：`对话/会话 · 流式输出（POST /chat-stream）`。"""
    return f"{semantic}（{name}）" if semantic else name


def _fp_description(ftype: str, semantic: str, name: str, impl: str) -> str:
    """业务化描述：把「后端接口 POST /x」升级为带业务语义的一句话。"""
    kind = {
        FType.API.value: "接口",
        FType.PAGE.value: "页面路由",
        FType.COMPONENT.value: "交互组件",
        FType.BUSINESS.value: "业务函数",
    }.get(ftype, "功能点")
    tail = f"；实现参考 {impl}" if impl else ""
    return f"{semantic}：{kind} {name}{tail}"


def _enrich_api_fp(fp: dict, symbols: dict) -> None:
    """A1：为 api 功能点补业务语义（业务域/动作/实现函数/源码位置）。"""
    method, path = fp.get("method", ""), fp.get("path", "")
    biz = _biz_label(_module_of(path))
    act = _act_of(method, path)
    meta = symbols.get((method, path)) or symbols.get((method.upper(), path)) or {}
    impl = ""
    if meta:
        impl = meta.get("func", "")
        if meta.get("doc"):
            impl = f"{impl}：{meta['doc']}"
        fp["loc"] = {"start": meta.get("sl"), "end": meta.get("se")}
    else:
        fp["loc"] = None
    fp["module"] = biz
    fp["action"] = act
    fp["semantic"] = f"{biz} · {act}"
    fp["impl"] = impl
    fp["title"] = _fp_title(fp["semantic"], fp["name"])
    fp["description"] = _fp_description(FType.API.value, fp["semantic"], fp["name"], impl)


def _enrich_plain_fp(fp: dict, biz: str, act: str) -> None:
    """A1：为 page / component 功能点补业务语义（无实现函数可依据）。"""
    fp["module"] = biz
    fp["action"] = act
    fp["semantic"] = f"{biz} · {act}"
    fp["impl"] = ""
    fp["loc"] = None
    fp["title"] = _fp_title(fp["semantic"], fp["name"])
    fp["description"] = _fp_description(
        fp["ftype"], fp["semantic"], fp.get("route") or fp["name"], ""
    )


def _enrich_fps(fps, rel: str, text: str, index=None) -> list:
    """A1：给一批功能点补 fp_id + 业务语义（就地修改并返回）。"""
    symbols = None
    for fp in fps:
        ftype = fp["ftype"]
        if ftype == FType.API.value:
            if symbols is None:
                symbols = (
                    index.symbols(rel) if index is not None else _parse_file_symbols(text or "")
                )
            _enrich_api_fp(fp, symbols)
        elif ftype == FType.PAGE.value:
            _enrich_plain_fp(fp, "前端页面", "页面可达")
        else:
            _enrich_plain_fp(fp, "前端组件", "交互触发")
        fp["fp_id"] = fp_id_of(ftype, fp["file_path"], fp["name"])
    return fps


class _SourceIndex:
    """C1 去重扫描索引：同一个文件「只读一次、只解析一次 AST」。

    A1(功能点业务语义) / 测试点派生 / B1(hunk 级打标) 三方共用同一份源码与符号表，
    避免同一仓库被各阶段反复读取与解析（此前每个阶段各自 read + ast.parse）。

    `aligned=True` 时改用 `git show target:rel` 取目标版本内容，使 AST 符号行号与
    `git diff -U0` 的 hunk 行号严格对齐（仅在 hunk 打标时、且只对变更文件使用）。
    """

    def __init__(self, root: str, target: str | None = None):
        self.root = str(root)
        self.target = target
        self._text: dict = {}  # 工作树版本：rel -> text|None
        self._text_t: dict = {}  # 目标版本(git show)：rel -> text|None
        self._sym: dict = {}  # (rel, aligned) -> symbols
        self.stats = {
            "files_read": 0,
            "ast_parses": 0,
            "text_requests": 0,
            "text_cache_hits": 0,
            "sym_cache_hits": 0,
            "git_show_calls": 0,
            "git_show_hits": 0,
            "worktree_reads": 0,
        }

    def _use_target(self, aligned: bool) -> bool:
        return bool(aligned and self.target)

    def text(self, rel: str, aligned: bool = False):
        self.stats["text_requests"] += 1
        use_t = self._use_target(aligned)
        cache = self._text_t if use_t else self._text
        if rel in cache:
            self.stats["text_cache_hits"] += 1
            return cache[rel]
        txt = None
        if use_t:
            self.stats["git_show_calls"] += 1
            rc, out = _git_show(self.root, self.target, rel)
            if rc == 0 and out:
                txt = out
                self.stats["git_show_hits"] += 1
        if txt is None:
            try:
                txt = (Path(self.root) / rel).read_text(encoding="utf-8", errors="ignore")
                self.stats["worktree_reads"] += 1
            except Exception:
                txt = None
        cache[rel] = txt
        self.stats["files_read"] += 1
        return txt

    def symbols(self, rel: str, aligned: bool = False) -> dict:
        key = (rel, self._use_target(aligned))
        if key in self._sym:
            self.stats["sym_cache_hits"] += 1
            return self._sym[key]
        txt = self.text(rel, aligned=aligned)
        sym = _parse_file_symbols(txt) if txt else {}
        if txt:
            self.stats["ast_parses"] += 1
        self._sym[key] = sym
        return sym


# ===================== 标签：全量 / 更新 =====================
# 用途：区分「全量测试点」（完整回归集）与「本次拉取代码后，通过代码对比
# 识别出的变更测试点」。变更测试点 = 其底层 source 文件出现在 base..target
# 的 diff 变更文件集合中，打标签『更新』；其余打『全量』。


def _git_toplevel(repo_path: str) -> str:
    """返回 git 认定的仓库根目录；非 git 仓库返回空串。"""
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _git_repo_usable(repo_path: str) -> bool:
    """校验 repo_path 本身就是 git 仓库根（防止 .git 损坏时静默向上找到父仓库）。

    场景：被测目录的 .git 不完整时，`git -C <target>` 会一路向上命中**父仓库**，
    导致 diff 取到的是父仓库的变更文件（路径完全不同，却因 basename 兜底匹配
    被误判为『更新』）。此处先比对 toplevel 真实路径，不一致即判定不可用。
    """
    top = _git_toplevel(repo_path)
    if not top:
        return False
    try:
        return Path(top).resolve() == Path(repo_path).resolve()
    except Exception:
        return False


def compute_diff_changed_files(repo_path: str, base: str, target: str) -> set:
    """获取 base..target 的变更文件集合（相对仓库根的路径）。

    用于给测试点打『更新』标签：测试点的 source 命中此集合即视为本次变更测试点。
    git 不可用时返回空集（此时全部测试点标『全量』）。
    """
    if not _git_repo_usable(repo_path):
        return set()
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "diff", "--name-only", base, target],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if out.returncode != 0:
            return set()
        return {ln.strip() for ln in out.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def compute_diff_hunks(repo_path: str, base: str, target: str) -> dict:
    """获取 base..target 的逐文件 hunk 行范围（用于「hunk 级精准打标」）。

    返回 {new_rel_path: [(start, count), ...]}，其中 start/count 为 `-U0`
    格式 `@@ -a,b +c,d @@` 中 **目标版本(+侧)** 的起始行与连续行数。
    hunk 命中的行 = [start, start+count-1]。

    用于把「文件级」标签升级为「hunk 级」：测试点的底层符号（路由/函数）
    其源码行区间与任一 hunk 区间重叠 → 标『更新』，否则（文件改了但该函数没改）
    标『全量』，从而解决「整文件所有测试点都误标更新」的精度问题。
    git 不可用 / 解析失败返回 {}（调用方据此降级为文件级）。
    """
    if not _git_repo_usable(repo_path):
        return {}
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "diff", "-U0", base, target],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if out.returncode != 0:
            return {}
    except Exception:
        return {}
    hunks: dict = {}
    cur = None
    for line in out.stdout.splitlines():
        if line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", line)
            cur = m.group(1) if m else None
        elif line.startswith("@@"):
            ms = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if ms and cur is not None:
                start = int(ms.group(1))
                cnt = int(ms.group(2)) if ms.group(2) else 1
                hunks.setdefault(cur, []).append((start, cnt))
    return hunks


def _git_show(repo_path: str, target: str, rel: str):
    """读取 target 版本下某文件的文本内容（保证与 diff hunk 行号对齐）。"""
    try:
        out = subprocess.run(
            ["git", "-C", repo_path, "show", f"{target}:{rel}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return out.returncode, out.stdout
    except Exception:
        return 1, ""


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


# ===================== hunk 级精准打标（B1） =====================
# 文件级打标的缺陷：只要 source 文件出现在 diff 里，该文件派生的「全部」
# 测试点（如 server.py 的 74 个路由 × 多维度）全部被标『更新』，导致
# 「本次变更应回归的测试点」严重膨胀、聚焦失效。
# hunk 级：进一步判断「该测试点对应的具体符号（路由函数 / 业务函数）所在
# 源码行区间是否真的被本次 diff 的 hunk 覆盖」，覆盖才标『更新』。


def _route_decorator_info(dec) -> tuple:
    """从路由装饰器 AST 节点提取 (METHOD, path)。

    仅识别静态字符串路径的路由，如 @app.post("/chat")、@router.get("/x/{id}")。
    路径为变量拼接 / f-string 等无法静态求值时返回 None（交由兜底逻辑处理）。
    """
    if not isinstance(dec, ast.Call):
        return None
    f = dec.func
    if not isinstance(f, ast.Attribute):
        return None
    method = f.attr.lower()
    if method not in ("get", "post", "put", "delete", "patch", "options", "head"):
        return None
    if not dec.args:
        return None
    a0 = dec.args[0]
    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
        return (method.upper(), a0.value)
    return None


def _parse_file_symbols(text: str) -> dict:
    """AST 解析单文件文本 → {symbol_key: {"sl","se","func","doc"}}。

    symbol_key：路由为 (METHOD, path)；其余 def/class 为函数/类名。
    doc 取 docstring 首行（截断 80 字符），是业务语义的重要来源
    （开发者写的说明通常就是这个接口/函数的真实业务含义）。
    top 标记是否顶层符号（col_offset == 0），用于业务函数维度只取顶层定义。
    """
    symbols: dict = {}
    try:
        tree = ast.parse(text)
    except Exception:
        return symbols
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            raw_doc = ast.get_docstring(node) or ""
            first = raw_doc.strip().splitlines()[0].strip() if raw_doc.strip() else ""
            rec = {
                "sl": node.lineno,
                "se": node.end_lineno,
                "func": node.name,
                "doc": first[:80],
                "top": getattr(node, "col_offset", 1) == 0,
            }
            info = None
            for dec in node.decorator_list:
                info = _route_decorator_info(dec)
                if info:
                    break
            if info:
                symbols[info] = rec
            symbols[node.name] = rec
    return symbols


def _parse_symbol_spans(repo_root: str, rel: str, target: str | None = None) -> dict:
    """解析某文件的符号表（hunk 打标 + 业务语义共用）。

    返回 {key: {"sl","se","func","doc"}}，其中 sl/se 为起止行号。
    优先用 `git show target:rel` 读取目标版本源码（与 diff hunk 行号严格对齐）；
    无 target 或读取失败时回退到工作树文件。解析失败返回空 dict。
    """
    text = None
    if target:
        _, text = _git_show(repo_root, target, rel)
    if not text:
        p = Path(repo_root) / rel
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return {}
    return _parse_file_symbols(text)


def _match_changed_rel(src: str, changed_set) -> str:
    """把测试点的 source 解析为 changed_set 中精确匹配的相对路径；无匹配返回 None。"""
    if not changed_set or not src:
        return None
    s = src.strip()
    if s in changed_set:
        return s
    base = s.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if not base:
        return None
    for c in changed_set:
        cb = c.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if cb == base:
            return c
    return None


def _tag_point(
    r: dict, changed_files, hunks: dict, index: "_SourceIndex", target: str | None = None
) -> str:
    """hunk 级标签判定，返回 Tag.UPDATE.value / Tag.FULL.value。

    规则：
      1) source 不在变更集 → 全量；
      2) source 在变更集，但无法定位 hunk / 无法解析符号 → 安全兜底为『更新』
         （保证不漏标真实的变更点，仅可能少量过标）；
      3) source 在变更集且解析到符号行区间 → 与 hunk 区间做重叠判定，
         重叠则『更新』，否则（文件改了但该函数没改）『全量』；
      4) 前端类（PAGE/UI）无精准符号 → 沿用文件级（标『更新』）。
    """
    rel = _match_changed_rel(r.get("source", ""), changed_files)
    if rel is None:
        return Tag.FULL.value
    method = r.get("method")
    if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
        key = (method, r.get("area", ""))  # API 路由：(METHOD, path)
    elif method == MethodMarker.FUNC.value:
        key = r.get("area", "")  # 业务函数：函数名
    else:
        return Tag.UPDATE.value  # 前端：文件级兜底
    # aligned=True：用 git show target 版本解析符号，行号与 hunk 严格对齐
    rec = index.symbols(rel, aligned=True).get(key)
    if rec is None:
        return Tag.UPDATE.value  # 无法精准定位符号 → 安全文件级
    sl, se = rec["sl"], rec["se"]
    file_hunks = hunks.get(rel)
    if not file_hunks:
        # 文件确已变更，但拿不到 hunk 数据（离线 / 调用方未提供 diff_hunks /
        # 该文件无 hunk 条目）→ 降级为文件级：保守标『更新』，避免漏标真实变更点。
        return Tag.UPDATE.value
    for hs, cnt in file_hunks:
        he = hs + cnt - 1
        if hs <= se and sl <= he:  # 符号行区间与 hunk 区间重叠
            return Tag.UPDATE.value
    return Tag.FULL.value


# ===================== 业务语义增强（B2） =====================
# 原测试点的 name/expect 是机械模板（"接口 POST /chat · 功能可用性" +
# "路由存在且可调用…"），下游（阶段3用例、阶段6报告）无法据此锚定业务场景。
# B2 为每条测试点补出：所属业务域、业务动作、实现函数与 docstring，
# 并据此重写 name / expect，使测试点"说人话、讲业务"。


def _enrich_semantic(r: dict, index: "_SourceIndex") -> None:
    """为单条测试点补充业务语义：semantic / impl / name / expect。

    API ：业务域=模块中文名；业务动作=路径关键词→HTTP 方法；
          附带路由实现函数名与其 docstring 作为「实现参考」。
    FUNC：业务域=核心模块业务名；附带函数 docstring。
    前端：业务语义=页面可达 / 组件交互。
    """
    method = r.get("method")
    area = r.get("area", "")
    rel = r.get("source", "")
    if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
        biz = _biz_label(_module_of(area))
        act = _act_of(method, area)
        meta = index.symbols(rel).get((method, area), {})
        impl = ""
        if meta:
            impl = meta.get("func", "")
            if meta.get("doc"):
                impl = f"{impl}：{meta['doc']}"
        r["semantic"] = f"{biz} · {act}"
        r["impl"] = impl
        r["name"] = f"{biz}·{act}（{method} {area}）· {r['dimension']}"
        r["expect"] = _expect_for(r["tp_type"], r["dimension"], biz, act, method, area, impl)
    elif method == MethodMarker.FUNC.value:
        mod = rel.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        biz = _CORE_MODULE_BIZ.get(mod, "业务逻辑")
        meta = index.symbols(rel).get(area, {})
        doc = meta.get("doc", "")
        r["semantic"] = f"{biz} · {area}"
        r["impl"] = f"{area}：{doc}" if doc else area
        r["name"] = f"{mod}::{area} — {doc or (biz + '逻辑覆盖')}"
        r["expect"] = _expect_func(biz, area, doc)
    else:
        kind = (
            MethodMarker.PAGE.value if method == MethodMarker.PAGE.value else MethodMarker.UI.value
        )
        r["semantic"] = (
            "前端页面 · 可达性" if kind == MethodMarker.PAGE.value else "前端组件 · 交互"
        )
        r["impl"] = ""
        r["name"] = f"{'页面可达' if kind == MethodMarker.PAGE.value else '交互组件'} {area}"
        r["expect"] = _expect_ui(kind, area)


class _ComprehensiveBuilder:
    """把 code_analyzer.analyze() 的基础功能点，扩成全面测试点。"""

    def build(
        self,
        local_path: str,
        project_type: str = "pc",
        changed_files=None,
        scopes=None,
        diff_hunks=None,
        diff_target=None,
    ) -> dict:
        # C1 去重扫描：功能点提取 / 业务语义 / 测试点派生 / hunk 打标 共用同一索引
        index = _SourceIndex(local_path, target=diff_target)
        base = code_analyzer.analyze(local_path, project_type, index)
        api_fps = [f for f in base if f["ftype"] == FType.API.value]
        page_fps = [f for f in base if f["ftype"] == FType.PAGE.value]
        comp_fps = [f for f in base if f["ftype"] == FType.COMPONENT.value]

        def _link(tps, fp):
            """A2：把测试点挂到来源功能点上（TP → FP 方向追溯）。"""
            for t in tps:
                t["fp_id"] = fp["fp_id"]
                t["fp_name"] = fp["name"]
                t["fp_title"] = fp.get("title", fp["name"])
            return tps

        raw = []
        # ① API 路由 → 四维展开（优先用统一契约的结构化 method/path 字段）
        for f in api_fps:
            method = f.get("method") or "GET"
            path = f.get("path") or f["name"].split(" ", 1)[-1]
            module = _module_of(path)
            raw += _link(self._expand_api(method, path, f["file_path"], module), f)
        # ② 核心业务模块函数（与功能点同源于一次 AST 扫描）
        b_tps, business_fps = self._expand_business(local_path, index)
        raw += b_tps
        # ③ 前端页面可达
        for f in page_fps:
            raw += _link(
                [
                    {
                        "module": "前端 Frontend",
                        "area": f.get("route") or f["name"],
                        "method": MethodMarker.PAGE.value,
                        "tp_type": TPType.NORMAL.value,
                        "name": f"页面可达 {f['name']}",
                        "dimension": Dimension.PAGE_REACH.value,
                        "source": f["file_path"],
                        "expect": "路由在 router 中定义且可导航加载，无白屏/404",
                    }
                ],
                f,
            )
        # ④ 组件交互
        for f in comp_fps:
            raw += _link(
                [
                    {
                        "module": "前端 Frontend",
                        "area": f["name"],
                        "method": MethodMarker.UI.value,
                        "tp_type": TPType.NORMAL.value,
                        "name": f"交互组件 {f['name']}",
                        "dimension": Dimension.INTERACTIVE.value,
                        "source": f["file_path"],
                        "expect": "组件含交互钩子(@click/按钮/表单/上传)，可正常触发",
                    }
                ],
                f,
            )

        # 统一功能点清单（C1 契约）：api/page/component + business
        functional_points = []
        seen_fp = set()
        for fp in list(api_fps) + list(page_fps) + list(comp_fps) + list(business_fps):
            if fp["fp_id"] in seen_fp:
                continue
            seen_fp.add(fp["fp_id"])
            functional_points.append(fp)

        # ===== B2：业务语义增强（在范围过滤与打标之前，保证全量一致）=====
        for r in raw:
            _enrich_semantic(r, index)
            # 注入执行层（VerifyLayer）：由来源种类推导默认层（接口/UI）
            r["verify_layer"] = derive_verify_layer(method_kind(r.get("method"))).value

        # 范围过滤（Scope）：仅保留测试类型(tp_type)落在 scopes 内的测试点。
        # - scopes=None            → 不过滤（兼容旧行为，生成全部四种类型）。
        # - scopes=set(...)        → 旧式：仅按 tp_type 过滤（向后兼容）。
        # - scopes=ScopeSpec(...)  → 新式：tp_types 过滤 + 可选 kinds 来源过滤
        #   （kinds 仅通用来源过滤；「接口」执行层选择见 VerifyLayer，不由范围关键词控制）。
        if scopes is not None:
            if isinstance(scopes, ScopeSpec):
                raw = [r for r in raw if r["tp_type"] in scopes.tp_types]
                if scopes.kinds is not None:
                    raw = [r for r in raw if _kind_of(r) in scopes.kinds]
            else:
                raw = [r for r in raw if r["tp_type"] in scopes]

        # 标签：hunk 级精准打标（B1）。
        # 有 diff_hunks 时按「符号行区间 ∩ hunk 区间」判定；无 hunk 数据
        # （离线 / 解析失败）时 _tag_point 自动降级为文件级，行为向后兼容。
        hunks = diff_hunks or {}
        for r in raw:
            r["tag"] = _tag_point(r, changed_files, hunks, index, diff_target)

        # 统一编号 + 模块汇总
        for i, r in enumerate(raw, 1):
            r["id"] = f"TP-{i:03d}"
        modules = {}
        for r in raw:
            m = r["module"]
            modules.setdefault(
                m,
                {
                    FType.API.value: 0,
                    FType.BUSINESS.value: 0,
                    "frontend": 0,
                    "total": 0,
                    "areas": set(),
                    "updated": 0,
                },
            )
            modules[m]["total"] += 1
            modules[m]["areas"].add(r["area"])
            if r["method"] in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
                modules[m][FType.API.value] += 1
            elif r["method"] in (MethodMarker.PAGE.value, MethodMarker.UI.value):
                modules[m]["frontend"] += 1
            else:
                modules[m][FType.BUSINESS.value] += 1
            if r["tag"] == Tag.UPDATE.value:
                modules[m]["updated"] += 1
        module_summary = []
        for m, v in modules.items():
            module_summary.append(
                {
                    "module": m,
                    "total": v["total"],
                    FType.API.value: v[FType.API.value],
                    FType.BUSINESS.value: v[FType.BUSINESS.value],
                    "frontend": v["frontend"],
                    "updated": v["updated"],
                    "area_count": len(v["areas"]),
                    "areas": sorted(v["areas"])[:12],
                }
            )
        module_summary.sort(key=lambda x: -x["total"])

        by_type = {}
        for r in raw:
            by_type[r["tp_type"]] = by_type.get(r["tp_type"], 0) + 1

        by_tag = {}
        for r in raw:
            by_tag[r["tag"]] = by_tag.get(r["tag"], 0) + 1

        # ===== A2 双向追溯：FP ⇄ TP =====
        fp_index = {}
        for fp in functional_points:
            # 保留功能点完整契约字段（module/action/semantic/impl/loc/…）+ 追溯索引
            node = dict(fp)
            node["test_points"] = []
            fp_index[fp["fp_id"]] = node
        orphan = 0  # 无来源功能点的测试点（契约完整性：应为 0）
        for r in raw:
            fid = r.get("fp_id")
            node = fp_index.get(fid)
            if node is None:
                orphan += 1
                continue
            node["test_points"].append(r["id"])
        covered = sum(1 for v in fp_index.values() if v["test_points"])
        fp_total = len(fp_index)
        traceability = {
            "fp_total": fp_total,
            "tp_total": len(raw),
            "fp_with_tp": covered,
            "fp_without_tp": fp_total - covered,
            "tp_with_fp": len(raw) - orphan,
            "tp_without_fp(orphan)": orphan,
            "coverage": f"{(covered / fp_total * 100):.1f}%" if fp_total else "0%",
            "max_tp_per_fp": max((len(v["test_points"]) for v in fp_index.values()), default=0),
            "note": (
                "fp_without_tp>0 通常为 Scope 过滤导致（如本轮只要正常+异常，"
                "安全/边界维度的派生测试点被过滤），非追溯断链；"
                "tp_without_fp 应恒为 0，非 0 即契约缺陷。"
            ),
        }
        # 功能点按派生测试点数降序（便于直接看「高价值功能点」）
        fp_rank = sorted(fp_index.values(), key=lambda v: (-len(v["test_points"]), v["name"]))
        for v in fp_rank:
            v["tp_count"] = len(v["test_points"])

        return {
            "contract_version": FP_CONTRACT_VERSION,
            "total": len(raw),
            "by_type": by_type,
            "by_tag": by_tag,
            "module_summary": module_summary,
            "test_points": raw,
            "functional_points": fp_rank,
            "fp_index": fp_index,
            "traceability": traceability,
            "scan_stats": index.stats,
        }

    def _expand_api(self, method, path, file_path, module):
        tps = [
            {
                "module": module,
                "area": path,
                "method": method,
                "tp_type": TPType.NORMAL.value,
                "name": f"接口 {method} {path} · 功能可用性",
                "dimension": Dimension.AVAIL.value,
                "source": file_path,
                "expect": "路由存在且可调用，携带合法凭证返回预期结构(2xx)",
            },
            {
                "module": module,
                "area": path,
                "method": method,
                "tp_type": TPType.SECURITY.value,
                "name": f"接口 {method} {path} · 鉴权校验",
                "dimension": Dimension.AUTH_MISS.value,
                "source": file_path,
                "expect": "缺失/错误 Authorization → 401/403，不泄露业务数据",
            },
            {
                "module": module,
                "area": path,
                "method": method,
                "tp_type": TPType.BOUNDARY.value,
                "name": f"接口 {method} {path} · 参数校验",
                "dimension": Dimension.PARAM_ILLEGAL.value,
                "source": file_path,
                "expect": "缺失必填参数 → 422/400；非法类型/越界值 → 400",
            },
        ]
        if _ID_PARAM_RE.search(path):
            tps.append(
                {
                    "module": module,
                    "area": path,
                    "method": method,
                    "tp_type": TPType.ABNORMAL.value,
                    "name": f"接口 {method} {path} · 资源不存在",
                    "dimension": Dimension.RES_NOT_FOUND.value,
                    "source": file_path,
                    "expect": "访问不存在/非法的 {id} → 404，错误信息友好",
                }
            )
        # 写操作补充越权维度
        if method in ("PUT", "PATCH", "DELETE") and _ID_PARAM_RE.search(path):
            tps.append(
                {
                    "module": module,
                    "area": path,
                    "method": method,
                    "tp_type": TPType.SECURITY.value,
                    "name": f"接口 {method} {path} · 越权访问",
                    "dimension": Dimension.PRIV_ESC.value,
                    "source": file_path,
                    "expect": "操作他人资源 → 403，不越权修改",
                }
            )
        return tps

    def _expand_business(self, local_path: str, index: "_SourceIndex"):
        """核心业务模块函数 → (测试点, business 功能点)。

        C1：与功能点提取共用 `_SourceIndex` 的同一份 AST 符号表（不再二次 read+parse），
        同一份符号同时产出「业务功能点」与「业务测试点」，天然保证两者可双向追溯。

        模块来源：`discover_business_modules()` —— 显式清单优先 + 动态发现补足，
        解决后端重构成 tools/** 后业务函数维度命中 0 的问题。
        """
        tps, fps = [], []
        for rel, biz, tops in discover_business_modules(local_path, index):
            # 末两级路径作模块短名：既可读，又避免同名文件（如两个 models.py）产生
            # 相同 fp_id 被去重吞掉
            parts = rel.split("/")
            mod = "/".join(parts[-2:]) if len(parts) >= 2 else rel
            module_label = f"业务函数·{biz}"
            for _, s, v in tops[:_BUSINESS_MAX_SYMBOLS]:
                doc = v.get("doc", "")
                impl = f"{s}：{doc}" if doc else s
                name = f"{mod}::{s}"
                tps.append(
                    {
                        "module": module_label,
                        "area": s,
                        "method": MethodMarker.FUNC.value,
                        "tp_type": TPType.NORMAL.value,
                        "name": f"{name} 业务覆盖",
                        "dimension": Dimension.BIZ_LOGIC.value,
                        "source": rel,
                        "expect": "函数/类可被调用且输入合法时输出符合预期（单测/集成覆盖）",
                        "fp_id": fp_id_of(FType.BUSINESS.value, rel, name),
                    }
                )
                fps.append(
                    {
                        "fp_id": fp_id_of(FType.BUSINESS.value, rel, name),
                        "ftype": FType.BUSINESS.value,
                        "name": name,
                        "title": f"{biz} · {s}" + (f"（{doc}）" if doc else ""),
                        "description": _fp_description(
                            FType.BUSINESS.value, f"{biz} · {s}", name, impl
                        ),
                        "file_path": rel,
                        "module": biz,
                        "action": s,
                        "semantic": f"{biz} · {s}",
                        "impl": impl,
                        "loc": {"start": v.get("sl"), "end": v.get("se")},
                    }
                )
        return tps, fps


def generate_comprehensive_test_points(
    local_path: str,
    project_type: str = "pc",
    changed_files=None,
    scopes=None,
    diff_hunks=None,
    diff_target=None,
) -> dict:
    """独立入口：对完整代码生成全面测试点（v2）。

    changed_files: 可选，base..target 的变更文件集合（相对仓库根路径）。
        提供后会为每个测试点打『更新/全量』标签，便于筛选本次变更测试点。
    scopes: 可选，测试点范围。
        - None          → 不过滤，生成全部四种行为类型（兼容旧行为）
        - set(...)      → 旧式，直接按 tp_type 过滤（向后兼容）
        - ScopeSpec(...)→ 新式范围描述符：
            · tp_types: 行为维度子集 {TPType.NORMAL.value,TPType.ABNORMAL.value,TPType.SECURITY.value,TPType.BOUNDARY.value}
            · kinds:    来源种类过滤；None=不限，{FType.API.value}=仅接口(HTTP 路由)来源
              （注：「接口」现为执行层枚举 VerifyLayer，非范围关键词；此处仅保留通用来源过滤能力）
              （「接口」为可选范围值，对应已有的接口型测试点/用例）
        - 默认（resolve_scope 未命中具体范围）＝ {TPType.NORMAL.value,TPType.BOUNDARY.value}（skill 当前默认范围）
        - {TPType.SECURITY.value,TPType.BOUNDARY.value} → 仅安全 + 边界
        过滤在「四维展开」之后、打标签/编号/汇总之前完成，使下游统计一致。
    diff_hunks: 可选，compute_diff_hunks() 返回的逐文件 hunk 行范围。
        提供后启用 **hunk 级精准打标（B1）**——仅当测试点对应的具体符号
        （路由/函数）源码行区间被本次 diff 的 hunk 覆盖时才标『更新』，
        解决文件级「整文件所有测试点都误标更新」的精度问题。缺失时降级为
        文件级（向后兼容，不报错）。
    diff_target: 可选，diff 的 target ref（如 test-20260907）。
        用于 `git show target:rel` 读取目标版本源码，使 AST 符号行号与
        diff hunk 行号严格对齐（避免工作树漂移导致误判）。
    返回 dict 除既有字段（total/by_type/by_tag/module_summary/test_points）外，
    按统一契约（C1 v1.0）新增：
        contract_version  契约版本
        functional_points 统一功能点清单（api/page/component/business，含 A1 业务语义）
        fp_index          {fp_id: {...,  "test_points": [TP-xxx]}}（FP → TP 追溯）
        traceability      FP ⇄ TP 覆盖统计（含孤儿测试点数，应恒为 0）
        scan_stats        去重扫描统计（同文件只读一次 / 只解析一次 AST 的证据：
                          text_requests > files_read 说明重复请求已被缓存吸收）
    """
    return _ComprehensiveBuilder().build(
        local_path, project_type, changed_files, scopes, diff_hunks, diff_target
    )


code_analyzer = CodeAnalyzer()
