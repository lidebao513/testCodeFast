"""引擎 · 模块三：测试点展开（tp_expand）。

把每条功能点按「行为维度」展开成若干测试点：
  正常（功能可用性） / 异常（资源或状态异常） / 安全（鉴权与越权） / 边界（参数边界）

与 legacy 的差异（有意修正）：
- `tp_id` 由「枚举序号」改为**内容指纹**（契约缺陷 D-2），同一份代码重复跑编号不变；
- 展开规则集中在 `dimensions_of()`，一眼可见，不再散落在 1500 行里。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from core.contracts import FunctionalPoint, TestPoint, tp_id_of, verify_layer_of_ftype
from core.enums import DEFAULT_SCOPE, AuthMode, Dimension, FType, MethodMarker, Tag, TPType
from engine import auth_scan
from engine.fp_extract import expect_of


# 路径参数（如 `/invoices/{invoice_id}`）
_PATH_PARAM_RE = re.compile(r"\{[^}]+\}")

# 「越权」维度只针对**修改他人资源**的操作（与 legacy 一致）
_PRIV_ESC_METHODS: tuple[str, ...] = ("PUT", "PATCH", "DELETE")

# 非 HTTP 来源 → method 字段标记（契约：PAGE/UI/FUNC，见 enums.MethodMarker）
_MARKER_BY_FTYPE: dict[str, str] = {
    FType.PAGE.value: MethodMarker.PAGE.value,
    FType.UI.value: MethodMarker.UI.value,
    FType.COMPONENT.value: MethodMarker.UI.value,
    FType.BUSINESS.value: MethodMarker.FUNC.value,
}

_SEMANTIC_ACTION: dict[str, str] = {
    TPType.NORMAL.value: "验证功能可用性",
    TPType.ABNORMAL.value: "验证异常路径处理",
    TPType.SECURITY.value: "验证鉴权与越权防护",
    TPType.BOUNDARY.value: "验证参数边界与非法输入",
}

# 维度规范顺序（与 enums.TPType 声明顺序一致）。
# 用途：生成 tp_id 的 ordinal 时取**规范顺序里的固定位置**，而不是循环下标。
# 为什么必须这样：循环下标是**过滤后**的序号，用户这次只要「正常+异常」、
# 下次加上「安全」，同一条『异常』测试点的序号就会从 1 变 2 → tp_id 漂移 →
# 旧用例被判 obsolete、新建一条，人工审核结论与执行历史全部断链（契约缺陷 D-9）。
_CANONICAL_ORDER: tuple[str, ...] = (
    TPType.NORMAL.value,
    TPType.ABNORMAL.value,
    TPType.SECURITY.value,
    TPType.BOUNDARY.value,
)

# 「行为维度 × 子维度」在规范顺序中的槽位：
# 「安全」维度下同时存在「鉴权缺失」与「越权」两条，需靠槽位区分（否则 tp_id 撞号）。
_DIMENSION_SLOTS: dict[str, dict[str, int]] = {
    TPType.NORMAL.value: {
        Dimension.AVAIL.value: 0,
        Dimension.BIZ_LOGIC.value: 0,
        Dimension.PAGE_REACH.value: 0,
        Dimension.INTERACTIVE.value: 0,
    },
    TPType.ABNORMAL.value: {Dimension.RES_NOT_FOUND.value: 0},
    TPType.SECURITY.value: {Dimension.AUTH_MISS.value: 0, Dimension.PRIV_ESC.value: 1},
    TPType.BOUNDARY.value: {Dimension.PARAM_ILLEGAL.value: 0},
}
_ORDINAL_STRIDE = 10


def _ordinal_of(category: str, dimension: str) -> int:
    """(维度, 子维度) 在规范顺序中的固定位置（与请求范围无关，保证 tp_id 稳定）。"""
    base = _CANONICAL_ORDER.index(category) if category in _CANONICAL_ORDER else 0
    slot = _DIMENSION_SLOTS.get(category, {}).get(dimension, 0)
    return base * _ORDINAL_STRIDE + slot


@dataclass
class ExpandContext:
    """展开上下文：范围过滤 + 标签 + 审核门 + 鉴权画像（F8）。"""

    scopes: set[str] = field(default_factory=lambda: set(DEFAULT_SCOPE))
    default_tag: str = Tag.FULL.value
    review_status: str = "pending"
    module_filter: set[str] = field(default_factory=set)
    max_per_fp: int = 8
    # F8：鉴权接线画像（`engine.auth_scan.AuthProfile`）。为空时安全维度退回
    # 「应当鉴权」的保守口径（保持 v1.0 行为，不影响既有测试与产物）。
    auth_profile: Any = None


def _method_of(fp: FunctionalPoint) -> str:
    """从功能点机器键里取 HTTP 方法（如 "POST /api/x" → POST）。"""
    return fp.name.split(" ", 1)[0].upper() if " " in fp.name else ""


def _tp_method(fp: FunctionalPoint) -> str:
    """测试点 method 字段：接口取 HTTP 动词，其余取来源标记（PAGE/UI/FUNC）。

    case_gen 依赖该字段区分 api / e2e 与派发 kind，故非接口类**不可**回退成函数名。
    """
    if fp.ftype == FType.API.value:
        return _method_of(fp)
    return _MARKER_BY_FTYPE.get(fp.ftype, MethodMarker.FUNC.value)


def _area_of(fp: FunctionalPoint) -> str:
    """测试点定位字段：接口取 URL 路径，其余取符号/路由名（业务函数即函数名）。"""
    if fp.ftype == FType.API.value and " " in fp.name:
        return fp.name.split(" ", 1)[1]
    return fp.name


def _security_expect(dimension: str, auth_mode: str) -> str:
    """安全维度的预期文案（F8）：**来自代码事实**，不写死 401/403。

    三种模式的文案必须可区分——否则「判通过」会被读成「安全没问题」：
    - `ABSENT`：本就该公开 → 断言「可访问」；但要提示「如需鉴权应在代码接线」；
    - `OPTIONAL`：有接线但未配置即放行 → 未配置时属未鉴权暴露，仍按「应被拒」断言；
    - `REQUIRED`：正常鉴权 → 越权/无凭证均应被拒。
    """
    if auth_mode == AuthMode.ABSENT.value:
        return (
            "该接口未检测到鉴权接线（公开接口）→ 可正常访问且不泄露敏感字段；"
            "如需鉴权应在代码中接线（判据见 engine/auth_scan.py）"
        )
    if auth_mode == AuthMode.OPTIONAL.value:
        return (
            "鉴权接线为占位实现（未配置令牌即放行）→ 未配置时视为未鉴权暴露；"
            "配置令牌后无凭证访问应被拒（401/403），且不泄露资源内容"
        )
    if dimension == Dimension.PRIV_ESC.value:
        return "以他人身份/越权凭证操作该资源 → 403，且不产生越权修改"
    return "未携带或携带无效凭证时返回 401/403，且不泄露资源内容（越权访问同样被拒）"


def _expect_of(fp: FunctionalPoint, category: str, dimension: str = "", auth_mode: str = "") -> str:
    """按维度给出可判定的预期结果文案。

    安全维度的预期**来自代码事实**（F8）：`auth_mode` 由 `engine/auth_scan.py` 扫源码得出，
    不再写死 401/403——对本来就该公开的接口写死 401/403 会产出假失败。
    """
    if category == TPType.NORMAL.value:
        return expect_of(fp.ftype, fp.name, _method_of(fp))
    if category == TPType.ABNORMAL.value:
        return (
            "返回 4xx（资源不存在 404 / 状态非法 409），响应体为结构化错误信息，服务不抛未捕获异常"
        )
    if category == TPType.SECURITY.value:
        return _security_expect(dimension, auth_mode)
    return "参数缺失或越界时返回 400/422，校验信息明确指出非法字段"


def _semantic_of(fp: FunctionalPoint, category: str) -> str:
    return f"{_SEMANTIC_ACTION[category]}：{fp.title}"


def plan_of(fp: FunctionalPoint) -> list[tuple[str, str]]:
    """功能点 → [(行为维度, 子维度)]，**与 legacy 展开规则逐条对齐**（P1 契约冻结）。

    对齐表（顺序即产出顺序，也是 tp_id 序号的规范顺序）：

    | 来源      | 维度 | 子维度         | 条件                        |
    |-----------|------|----------------|-----------------------------|
    | api       | 正常 | 可用性         | 全部                        |
    | api       | 安全 | 鉴权缺失       | 全部                        |
    | api       | 边界 | 参数非法       | 全部                        |
    | api       | 异常 | 资源不存在     | 含路径参数 `{id}`           |
    | api       | 安全 | 越权           | 含 `{id}` 且方法为 PUT/PATCH/DELETE |
    | page      | 正常 | 页面可达       | 全部                        |
    | component | 正常 | 交互元素可用   | 全部                        |
    | business  | 正常 | 业务逻辑可用   | 全部                        |

    两条与 legacy 的有意差异（均已在代码注释说明）：
    - `component` 的来源扩展名加入 `.tsx/.jsx`（legacy 只认 `.vue`，React 仓一个都提不出来）；
    - 不再给 `page` 派生「边界」维度（页面无参数校验语义，属噪声）。
    """
    if fp.ftype == FType.API.value:
        method = _method_of(fp)
        has_id = bool(_PATH_PARAM_RE.search(fp.name))
        plan = [
            (TPType.NORMAL.value, Dimension.AVAIL.value),
            (TPType.SECURITY.value, Dimension.AUTH_MISS.value),
            (TPType.BOUNDARY.value, Dimension.PARAM_ILLEGAL.value),
        ]
        if has_id:
            plan.append((TPType.ABNORMAL.value, Dimension.RES_NOT_FOUND.value))
        if has_id and method in _PRIV_ESC_METHODS:
            plan.append((TPType.SECURITY.value, Dimension.PRIV_ESC.value))
        return plan
    if fp.ftype == FType.PAGE.value:
        return [(TPType.NORMAL.value, Dimension.PAGE_REACH.value)]
    if fp.ftype == FType.COMPONENT.value:
        return [(TPType.NORMAL.value, Dimension.INTERACTIVE.value)]
    return [(TPType.NORMAL.value, Dimension.BIZ_LOGIC.value)]


def dimensions_of(fp: FunctionalPoint) -> list[str]:
    """（兼容视图）某条功能点会展开出哪些行为维度。"""
    return [category for category, _ in plan_of(fp)]


def expand_functional_point(
    fp: FunctionalPoint,
    ctx: ExpandContext,
    *,
    ordinal_base: int = 0,
    tag: str | None = None,
) -> list[TestPoint]:
    """把一条功能点展开为测试点集合（已按 ctx.scopes 过滤）。"""
    method = _tp_method(fp)
    area = _area_of(fp)
    auth_mode = (
        auth_scan.mode_of_fp(fp, ctx.auth_profile)
        if ctx.auth_profile is not None
        else AuthMode.REQUIRED.value
    )
    out: list[TestPoint] = []
    produced = 0
    for category, dimension in plan_of(fp):
        if category not in ctx.scopes:
            continue
        out.append(
            TestPoint(
                tp_id=tp_id_of(
                    fp.fp_id,
                    category,
                    area=area,
                    method=method,
                    dimension=dimension,
                    # 固定序号：与请求范围无关，保证「同一份代码，编号不变」
                    ordinal=ordinal_base + _ordinal_of(category, dimension),
                ),
                fp_contract_id=fp.fp_id,
                category=category,
                module=fp.module,
                title=f"[{category}] {fp.title}",
                semantic=_semantic_of(fp, category),
                source=fp.file_path,
                method=method,
                area=area,
                expect=_expect_of(fp, category, dimension, auth_mode),
                dimension=dimension,
                tag=tag or ctx.default_tag,
                review_status=ctx.review_status,
                verify_layer=verify_layer_of_ftype(fp.ftype),
            )
        )
        produced += 1
        if produced >= ctx.max_per_fp:
            break
    return out


def expand_all(
    fps: list[FunctionalPoint],
    ctx: ExpandContext | None = None,
    *,
    tag_by_fp: dict[str, str] | None = None,
) -> list[TestPoint]:
    """批量展开；`tag_by_fp` 为增量打标结果（fp_id → 全量/更新）。"""
    ctx = ctx or ExpandContext()
    tag_by_fp = tag_by_fp or {}
    out: list[TestPoint] = []
    for fp in fps:
        if ctx.module_filter and fp.module not in ctx.module_filter:
            continue
        out.extend(expand_functional_point(fp, ctx, tag=tag_by_fp.get(fp.fp_id)))
    return out


def scope_summary(tps: list[TestPoint]) -> dict[str, int]:
    """按行为维度汇总（供报告与验收）。"""
    out: dict[str, int] = {}
    for tp in tps:
        out[tp.category] = out.get(tp.category, 0) + 1
    return out
