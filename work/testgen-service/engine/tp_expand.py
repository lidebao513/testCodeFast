"""引擎 · 模块三：测试点展开（tp_expand）。

把每条功能点按「行为维度」展开成若干测试点：
  正常（功能可用性） / 异常（资源或状态异常） / 安全（鉴权与越权） / 边界（参数边界）

与 legacy 的差异（有意修正）：
- `tp_id` 由「枚举序号」改为**内容指纹**（契约缺陷 D-2），同一份代码重复跑编号不变；
- 展开规则集中在 `dimensions_of()`，一眼可见，不再散落在 1500 行里。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.contracts import FunctionalPoint, TestPoint, tp_id_of, verify_layer_of_ftype
from core.enums import Dimension, FType, MethodMarker, Tag, TPType
from engine.fp_extract import expect_of


# 需要「异常」维度的方法：写操作失败路径必须验证
_WRITE_METHODS: tuple[str, ...] = ("POST", "PUT", "PATCH", "DELETE")

# 非 HTTP 来源 → method 字段标记（契约：PAGE/UI/FUNC，见 enums.MethodMarker）
_MARKER_BY_FTYPE: dict[str, str] = {
    FType.PAGE.value: MethodMarker.PAGE.value,
    FType.UI.value: MethodMarker.UI.value,
    FType.COMPONENT.value: MethodMarker.UI.value,
    FType.BUSINESS.value: MethodMarker.FUNC.value,
}

# 维度 → 子维度（dimension）
_DIMENSION_BY_CATEGORY: dict[str, str] = {
    TPType.ABNORMAL.value: Dimension.RES_NOT_FOUND.value,
    TPType.SECURITY.value: Dimension.AUTH_MISS.value,
    TPType.BOUNDARY.value: Dimension.PARAM_ILLEGAL.value,
}

_SEMANTIC_ACTION: dict[str, str] = {
    TPType.NORMAL.value: "验证功能可用性",
    TPType.ABNORMAL.value: "验证异常路径处理",
    TPType.SECURITY.value: "验证鉴权与越权防护",
    TPType.BOUNDARY.value: "验证参数边界与非法输入",
}


@dataclass
class ExpandContext:
    """展开上下文：范围过滤 + 标签 + 审核门。"""

    scopes: set[str] = field(default_factory=lambda: {TPType.NORMAL.value, TPType.BOUNDARY.value})
    default_tag: str = Tag.FULL.value
    review_status: str = "pending"
    module_filter: set[str] = field(default_factory=set)
    max_per_fp: int = 8


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


def _dimension_of(category: str, fp: FunctionalPoint) -> str:
    if category == TPType.NORMAL.value:
        if fp.ftype == FType.BUSINESS.value:
            return Dimension.BIZ_LOGIC.value
        if fp.ftype == FType.PAGE.value:
            return Dimension.PAGE_REACH.value
        return Dimension.AVAIL.value
    return _DIMENSION_BY_CATEGORY.get(category, Dimension.AVAIL.value)


def _expect_of(fp: FunctionalPoint, category: str) -> str:
    """按维度给出可判定的预期结果文案。"""
    if category == TPType.NORMAL.value:
        return expect_of(fp.ftype, fp.name, _method_of(fp))
    if category == TPType.ABNORMAL.value:
        return (
            "返回 4xx（资源不存在 404 / 状态非法 409），响应体为结构化错误信息，服务不抛未捕获异常"
        )
    if category == TPType.SECURITY.value:
        return "未携带或携带无效凭证时返回 401/403，且不泄露资源内容（越权访问同样被拒）"
    return "参数缺失或越界时返回 400/422，校验信息明确指出非法字段"


def _semantic_of(fp: FunctionalPoint, category: str) -> str:
    return f"{_SEMANTIC_ACTION[category]}：{fp.title}"


def dimensions_of(fp: FunctionalPoint) -> list[str]:
    """某条功能点应展开出哪些行为维度（规则表，确定性）。"""
    cats = [TPType.NORMAL.value]
    if fp.ftype == FType.API.value:
        method = _method_of(fp)
        has_path_param = "{" in fp.name
        cats.append(TPType.SECURITY.value)
        if has_path_param or method in _WRITE_METHODS:
            cats.append(TPType.ABNORMAL.value)
        if has_path_param:
            cats.append(TPType.BOUNDARY.value)
    elif fp.ftype == FType.PAGE.value:
        cats.append(TPType.BOUNDARY.value)
    return cats


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
    out: list[TestPoint] = []
    idx = 0
    for category in dimensions_of(fp):
        if category not in ctx.scopes:
            continue
        dimension = _dimension_of(category, fp)
        out.append(
            TestPoint(
                tp_id=tp_id_of(
                    fp.fp_id,
                    category,
                    area=area,
                    method=method,
                    dimension=dimension,
                    ordinal=ordinal_base + idx,
                ),
                fp_contract_id=fp.fp_id,
                category=category,
                module=fp.module,
                title=f"[{category}] {fp.title}",
                semantic=_semantic_of(fp, category),
                source=fp.file_path,
                method=method,
                area=area,
                expect=_expect_of(fp, category),
                dimension=dimension,
                tag=tag or ctx.default_tag,
                review_status=ctx.review_status,
                verify_layer=verify_layer_of_ftype(fp.ftype),
            )
        )
        idx += 1
        if idx >= ctx.max_per_fp:
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
