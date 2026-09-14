"""引擎 · 模块二：功能点提取（fp_extract）。

从源码中提取「可测行为单元」：
  - api      后端 HTTP 路由（AST 解析装饰器，不做正则猜测）
  - business 后端公开业务函数
  - page     前端路由（js/ts/vue 中的 path 声明）

设计约束：
  - **不臆造**：只提取代码里真实存在的路由/函数，路径一律来自 AST 常量，猜不出来就丢弃；
  - 每条功能点携带 `file_path` + 行号证据（供上层做「证据引用」）；
  - `name` 是机器键（不可改），`title` 是业务化展示名。
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from core.contracts import FunctionalPoint, fp_id_of
from core.enums import BUSINESS_EXTRACT_STRICT, FType
from engine.scan import FRONTEND_EXTS, SourceFile


# FastAPI / Flask 风格的路由装饰器名
ROUTE_METHODS: dict[str, str] = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "delete": "DELETE",
    "patch": "PATCH",
    "options": "OPTIONS",
    "head": "HEAD",
}

# 前端路由：path: '/xxx' / path = "/xxx"
_PAGE_PATH_RE = re.compile(r"""\bpath\s*[:=]\s*["'`](/[^"'`]*)["'`]""")
# 前端组件名：name: 'Xxx'
_PAGE_NAME_RE = re.compile(r"""\bname\s*[:=]\s*["'`]([A-Za-z_][\w-]*)["'`]""")

# 交互钩子：出现即视为「关键交互组件」（兼容 React JSX 与 Vue 模板）
_UI_HOOK_RE = re.compile(
    r"(onClick\s*=|onChange\s*=|onSubmit\s*=|@click|v-on:|"
    r"<button|<input|<form|<select|<textarea|el-button|type=[\"']file)",
    re.IGNORECASE,
)
# 组件来源扩展名：.vue 为 legacy 原有；.tsx/.jsx 是 React 主战场，legacy 未覆盖
_COMPONENT_EXTS: tuple[str, ...] = (".tsx", ".jsx", ".vue")

# 屏幕目录：位于这些目录下的前端文件视为「页面/屏幕」（即使自身不写 path= 路由声明，
# 它也是被路由渲染出来的完整页面）。这是修复「UI 层偏少」的关键：原实现只认 `path=` 声明，
# 漏掉了所有「路由渲染出来的屏幕」（如 pages/mobile/MobileChatPage.tsx）。
_SCREEN_DIRS: tuple[str, ...] = ("pages", "views", "screens")
# 屏幕文件名：*Page / *Screen（React/Vue 常见命名）
_SCREEN_NAME_RE = re.compile(r".*(Page|Screen)\.(tsx|jsx|vue|ts|js)$")

_SKIP_FUNC_PREFIXES: tuple[str, ...] = ("_", "test_")


def _is_screen(rel: str, text: str) -> bool:
    """屏幕判定（宽松、可扩展）：命中任一即视为「页面/屏幕」。

    1) 声明了路由 `path=`（如 App.tsx 路由树、带自我路由的页面）；
    2) 位于 `pages/ views/ screens/` 目录；
    3) 文件名形如 `*Page` / `*Screen`。
    """
    if _PAGE_PATH_RE.search(text):
        return True
    parts = rel.split("/")
    if any(d in parts for d in _SCREEN_DIRS):
        return True
    return bool(_SCREEN_NAME_RE.search(parts[-1]))


def _has_ui_hooks(sf: SourceFile) -> bool:
    """是否含交互钩子（与 _extract_components 同源判定）。"""
    return bool(_UI_HOOK_RE.search(sf.text))


def _screen_fp(sf: SourceFile) -> FunctionalPoint:
    """为「无 path= 声明的屏幕文件」生成一条页面功能点（按文件名路由化）。"""
    stem = sf.name
    name = f"/{stem}" if not stem.startswith("/") else stem
    return FunctionalPoint(
        fp_id=fp_id_of(FType.PAGE.value, sf.rel, name),
        ftype=FType.PAGE.value,
        file_path=sf.rel,
        name=name,
        title=f"{module_of(sf.rel)} · 页面/{stem}",
        module=module_of(sf.rel),
        semantic=f"前端屏幕（{sf.rel}）",
        description=f"{sf.rel}",
    )


@dataclass
class ExtractResult:
    """提取结果 + 统计。"""

    functional_points: list[FunctionalPoint] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for fp in self.functional_points:
            out[fp.ftype] = out.get(fp.ftype, 0) + 1
        return out


# ---------------------------------------------------------------- 路径 → 模块名
def module_of(rel: str) -> str:
    """由文件路径推导业务模块名：取路径中最有信息量的那一段。"""
    parts = [p for p in rel.split("/") if p]
    if not parts:
        return "root"
    parts = parts[:-1] if "." in parts[-1] else parts
    # 跳过通用的目录层级
    generic = {"src", "app", "backend", "frontend", "server", "api", "core", "modules", "lib"}
    meaningful = [p for p in parts if p.lower() not in generic]
    return (meaningful[-1] if meaningful else (parts[-1] if parts else "root")) or "root"


# 写/删动词 → 标题动作名（表驱动，避免散落的 return 字面量）
_ACTION_BY_METHOD: dict[str, str] = {
    "POST": "创建",
    "PUT": "更新",
    "PATCH": "更新",
    "DELETE": "删除",
}


def _action_of(method: str, path: str) -> str:
    """由方法与路径推导动作名（用于标题）。"""
    m = method.upper()
    if m == "GET":
        return "查询详情" if "{" in path else "查询列表"
    return _ACTION_BY_METHOD.get(m, "调用")


# ---------------------------------------------------------------- 期望文案
# 期望文案：按 HTTP 方法给出（确定性，不依赖 LLM）
_API_EXPECT: dict[str, str] = {
    "POST": "返回 2xx，资源创建成功，响应体包含新建对象标识",
    "PUT": "返回 2xx，资源更新成功，字段值与请求一致",
    "PATCH": "返回 2xx，资源更新成功，字段值与请求一致",
    "DELETE": "返回 2xx（或 204），资源被删除，再次查询返回 404",
}
_EXPECT_BY_FTYPE: dict[str, str] = {
    FType.PAGE.value: "页面/路由可正常渲染，无白屏或控制台报错",
    FType.BUSINESS.value: "函数返回符合语义的结果，异常分支被正确捕获",
}


def expect_of(ftype: str, area: str, method: str = "") -> str:
    """确定性期望文案（人类可读；执行层后续解析具体状态码）。"""
    if ftype == FType.API.value:
        verb = (method or "GET").upper()
        if verb in _API_EXPECT:
            return _API_EXPECT[verb]
        if "{" in area:
            return "返回 2xx，响应体包含该资源的完整字段"
        return "返回 2xx，响应体为列表结构，分页字段可用"
    if ftype in _EXPECT_BY_FTYPE:
        return _EXPECT_BY_FTYPE[ftype]
    return "交互元素可用，点击后产生预期状态变化"


# ---------------------------------------------------------------- API 路由
def _node_call(node: ast.AST) -> ast.Call | None:
    return node if isinstance(node, ast.Call) else None


def _first_str_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _fastapi_route(node: ast.AST) -> tuple[str, str] | None:
    """FastAPI 风格：@router.get("/x") / @app.post("/y")。"""
    call = _node_call(node)
    if call is None or not isinstance(call.func, ast.Attribute):
        return None
    method = ROUTE_METHODS.get(call.func.attr.lower())
    if not method:
        return None
    path = _first_str_arg(call)
    return (method, path) if path is not None else None


def _flask_route(node: ast.AST) -> tuple[str, str] | None:
    """Flask 风格：@bp.route("/x", methods=["POST"])。"""
    call = _node_call(node)
    if call is None or not isinstance(call.func, ast.Attribute):
        return None
    if call.func.attr.lower() != "route":
        return None
    path = _first_str_arg(call)
    if path is None:
        return None
    return _declared_method(call), path


def _declared_method(call: ast.Call) -> str:
    """从 `methods=[...]` 关键字取第一个动词，缺省 GET。"""
    for kw in call.keywords:
        if kw.arg != "methods" or not isinstance(kw.value, ast.List):
            continue
        for elt in kw.value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                return elt.value.upper()
    return "GET"


def _route_decorator(node: ast.AST) -> tuple[str, str] | None:
    """解析装饰器，返回 (HTTP 方法, 路径)；非路由装饰器返回 None。"""
    return _fastapi_route(node) or _flask_route(node)


def _router_prefix(tree: ast.Module) -> str:
    """识别 `APIRouter(prefix="/api/v1")`，把前缀拼回路由路径。"""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        fn = node.value.func
        name = ""
        if isinstance(fn, ast.Name):
            name = fn.id
        elif isinstance(fn, ast.Attribute):
            name = fn.attr
        if name != "APIRouter":
            continue
        for kw in node.value.keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                return str(kw.value.value or "")
    return ""


def _docstring_summary(node: ast.AST) -> str:
    doc = (
        ast.get_docstring(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        else None
    )
    if not doc:
        return ""
    return doc.strip().splitlines()[0][:80]


def _qualified_names(tree: ast.Module) -> dict[int, str]:
    """`{id(函数节点): 限定名}`：类内方法带类名前缀（`Cls.method`），嵌套函数带外层前缀。

    为什么需要：业务功能点若只用**裸函数名**做机器键，同一文件里不同类的同名方法
    （如多处 `sort_key` / `put` / `flush`）会算出相同 `fp_id`，落库时被去重**静默合并**，
    导致不同行为共用一个编号、追溯串味。加类名前缀即消除该碰撞。
    """
    out: dict[int, str] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[id(child)] = prefix + child.name
                visit(child, f"{prefix}{child.name}.")
            else:
                visit(child, prefix)

    visit(tree, "")
    return out


# 业务噪声目录片段（仅用于「业务函数」级过滤，与 scan.NOISE_DIR_PARTS 不同）：
# 这些目录下的文件**整文件可能不被排除**（如 conf/schema 可能含真实 API），
# 但其内部「业务函数」不是被测产品的独立能力（测试套件/脚手架/构建脚本/配置模式），
# strict 模式下不计入业务功能点。regression/_fx_test/fixtures/scripts/selftest 虽也在本集合，
# 但它们已被 scan.NOISE_DIR_PARTS 整文件排除，此处仅作防御性冗余判定。
_BUSINESS_NOISE_DIR_PARTS: frozenset[str] = frozenset(
    {"regression", "_fx_test", "fixtures", "scripts", "selftest", "conf", "schema"}
)
_BUSINESS_NOISE_FILE_PREFIXES: tuple[str, ...] = ("test_", "conftest", "verify_", "selftest_")


def _file_is_business_noise(rel: str, mode: str, include_dirs: list[str]) -> bool:
    """判断某文件中的「业务函数」是否应被排除（不计入业务功能点）。

    - mode != "strict"：从不排除（保留 legacy 全量行为）。
    - mode == "strict"：命中业务噪声信号（目录片段 / 文件名前缀）则排除；
      但落在 include_dirs 白名单（如 tools/agents/mcp_servers）下的文件除外——
      这些目录被显式认定为独立能力来源，其业务函数应保留。
    """
    if mode != BUSINESS_EXTRACT_STRICT:
        return False
    rel_norm = rel.replace("\\", "/")
    parts = rel_norm.split("/")
    # 白名单优先：落在独立能力目录下，业务函数保留
    if any(
        rel_norm == d.rstrip("/") or rel_norm.startswith(d.rstrip("/") + "/") for d in include_dirs
    ):
        return False
    if parts[-1].startswith(_BUSINESS_NOISE_FILE_PREFIXES):
        return True
    return any(p in _BUSINESS_NOISE_DIR_PARTS for p in parts[:-1])


def _extract_api_and_business(
    sf: SourceFile,
    tree: ast.Module,
    business_extract_mode: str = BUSINESS_EXTRACT_STRICT,
    business_include_dirs: list[str] | None = None,
) -> list[FunctionalPoint]:
    module = module_of(sf.rel)
    prefix = _router_prefix(tree)
    qualnames = _qualified_names(tree)
    out: list[FunctionalPoint] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        route: tuple[str, str] | None = None
        for dec in node.decorator_list:
            route = _route_decorator(dec)
            if route:
                break
        if route:
            method, path = route
            full = (prefix + path) if prefix and path.startswith("/") else (path or prefix)
            full = full or "/"
            name = f"{method} {full}"
            summary = _docstring_summary(node)
            out.append(
                FunctionalPoint(
                    fp_id=fp_id_of(FType.API.value, sf.rel, name),
                    ftype=FType.API.value,
                    file_path=sf.rel,
                    name=name,
                    title=f"{module} · {_action_of(method, full)}{full}",
                    module=module,
                    semantic=summary or f"{method} {full}",
                    description=f"{node.name}() @ {sf.rel}:{node.lineno}",
                    commit_ref="",
                )
            )
            continue
        # 公开业务函数（无装饰器、非私有、非测试）
        if node.name.startswith(_SKIP_FUNC_PREFIXES):
            continue
        # P1 · 业务函数噪声过滤（strict 模式）：测试/脚手架/配置类文件中的函数排除，
        # 避免把测试套件/构建脚本/配置模式当成被测业务能力（详见 qa-test-points 技能 §十四）。
        if _file_is_business_noise(sf.rel, business_extract_mode, business_include_dirs or []):
            continue
        qname = qualnames.get(id(node), node.name)  # 机器键：类内方法带类名前缀，避免同名碰撞
        summary = _docstring_summary(node)
        out.append(
            FunctionalPoint(
                fp_id=fp_id_of(FType.BUSINESS.value, sf.rel, qname),
                ftype=FType.BUSINESS.value,
                file_path=sf.rel,
                name=qname,
                title=f"{module} · {qname}",
                module=module,
                semantic=summary or node.name.replace("_", " "),
                description=f"{qname}() @ {sf.rel}:{node.lineno}",
            )
        )
    return out


def _extract_pages(sf: SourceFile) -> list[FunctionalPoint]:
    """前端路由提取（基于 path 声明，识别 `path: '/x'` 与 JSX `path="/x"`）。"""
    if sf.is_noise:
        return []
    out: list[FunctionalPoint] = []
    seen: set[str] = set()
    names = _PAGE_NAME_RE.findall(sf.text)
    for i, path in enumerate(_PAGE_PATH_RE.findall(sf.text)):
        if path in seen:
            continue
        seen.add(path)
        label = names[i] if i < len(names) else sf.name
        out.append(
            FunctionalPoint(
                fp_id=fp_id_of(FType.PAGE.value, sf.rel, path),
                ftype=FType.PAGE.value,
                file_path=sf.rel,
                name=path,
                title=f"{module_of(sf.rel)} · 页面{path}",
                module=module_of(sf.rel),
                semantic=f"前端路由 {path}（{label}）",
                description=f"{sf.rel}",
            )
        )
    return out


def _extract_components(sf: SourceFile) -> list[FunctionalPoint]:
    """关键交互组件（启发式：含按钮/表单/上传/输入等交互钩子）。

    与 legacy 的差异（有意扩展）：legacy 只认 `.vue`，React 仓库（.tsx/.jsx）
    一个组件都提不出来 → UI 层只剩「页面可达」。这里把 React 一并纳入。
    """
    if sf.is_noise or sf.ext not in _COMPONENT_EXTS or not _UI_HOOK_RE.search(sf.text):
        return []
    return [
        FunctionalPoint(
            fp_id=fp_id_of(FType.COMPONENT.value, sf.rel, sf.name),
            ftype=FType.COMPONENT.value,
            file_path=sf.rel,
            name=sf.name,
            title=f"{module_of(sf.rel)} · 交互组件{sf.name}",
            module=module_of(sf.rel),
            semantic=f"含交互钩子的组件 {sf.rel}",
            description=f"{sf.rel}",
        )
    ]


# ---------------------------------------------------------------- 对外入口
def extract_functional_points(  # noqa: C901, PLR0913
    files: dict[str, SourceFile],
    *,
    include_business: bool = True,
    extract_pages: bool = True,
    extract_components: bool = True,
    business_extract_mode: str = BUSINESS_EXTRACT_STRICT,
    business_include_dirs: list[str] | None = None,
) -> ExtractResult:
    """从已扫描文件集中提取功能点（同文件只解析一次 AST）。"""
    result = ExtractResult()
    for rel in sorted(files):
        sf = files[rel]
        if sf.is_noise:
            continue
        try:
            if sf.is_python:
                tree = sf.tree()
                if tree is None:
                    result.errors.append(f"{rel}: AST 解析失败，已跳过")
                    continue
                fns = _extract_api_and_business(
                    sf, tree, business_extract_mode, business_include_dirs
                )
                if not include_business:
                    fns = [f for f in fns if f.ftype == FType.API.value]
                result.functional_points.extend(fns)
            elif sf.ext in FRONTEND_EXTS:
                # 单文件单决策：屏幕优先判定为「页面」，否则（含交互钩子）判为「交互组件」。
                # 避免一个屏幕文件同时产出「页面 + 组件」两条 UI 功能点造成重复。
                if extract_pages and _is_screen(sf.rel, sf.text):
                    pages = _extract_pages(sf)
                    if not pages:
                        pages = [_screen_fp(sf)]
                    result.functional_points.extend(pages)
                elif extract_components and _has_ui_hooks(sf):
                    result.functional_points.extend(_extract_components(sf))
        except (SyntaxError, ValueError, AttributeError) as exc:
            result.errors.append(f"{rel}: {type(exc).__name__}: {exc}")
    return result
