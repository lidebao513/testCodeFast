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
from core.enums import FType
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

_SKIP_FUNC_PREFIXES: tuple[str, ...] = ("_", "test_")


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


def _extract_api_and_business(sf: SourceFile, tree: ast.Module) -> list[FunctionalPoint]:
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


# ---------------------------------------------------------------- 对外入口
def extract_functional_points(
    files: dict[str, SourceFile],
    *,
    include_business: bool = True,
    extract_pages: bool = True,
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
                fns = _extract_api_and_business(sf, tree)
                if not include_business:
                    fns = [f for f in fns if f.ftype == FType.API.value]
                result.functional_points.extend(fns)
            elif extract_pages and sf.ext in FRONTEND_EXTS:
                result.functional_points.extend(_extract_pages(sf))
        except (SyntaxError, ValueError, AttributeError) as exc:
            result.errors.append(f"{rel}: {type(exc).__name__}: {exc}")
    return result
