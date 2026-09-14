"""引擎 · 模块六：用例生成（case_gen）。

测试点 → 用例，契约 v1.0 的八要素在此落地：
  编号(tc_no) / 模块(module) / 标题(title) / 类型(case_type) /
  优先级(priority) / 前置(precondition) / 步骤(doc_steps) / 预期(steps[0].expect)

**确定性为主**：不依赖 LLM；同一输入重复生成结果完全一致（配合 store 侧幂等对账）。
**机器步只在 steps[0]**：执行器只读第一步，其余人类可读步骤写入 `doc_steps`。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.contracts import (
    CaseSpec,
    TestPoint,
    precondition_of,
    priority_of,
    verify_layer_of_ftype,
)
from core.enums import (
    COVERAGE_ROLE_PRIMARY,
    COVERAGE_ROLE_SUPPLEMENT,
    LAYER_STRATEGY_UI_FIRST,
    FType,
    TPType,
    VerifyLayer,
    method_kind,
)


def _get(tp: Any, key: str, default: Any = "") -> Any:
    value = tp.get(key, default) if isinstance(tp, Mapping) else getattr(tp, key, default)
    return default if value is None else value


def _method_kind(method: str) -> tuple[bool, str]:
    """返回 (是否接口类, kind)。

    kind 一律是 FType 取值（`api`/`page`/`ui`/`business`），**不留空串**：
    早期实现给 HTTP 路由返回 `""`，导致下游按 `steps[0].kind` 分组时
    整类 HTTP 接口用例被漏掉（空值既不等于 api 也不等于 business）。
    """
    kind = method_kind(method)
    return kind == FType.API.value, kind


def build_doc_steps(tp: Any, precondition: str, layer: str) -> list[dict[str, Any]]:
    """人类可读四步：前置 → 准备 → 执行 → 断言。

    文案必须与**执行层**一致：页面/组件不是「请求」，业务函数也不是「请求」，
    早期实现一律写成「构造请求：PAGE /」「发送 FUNC main 请求」，并统一断言
    「响应状态码符合预期」——对 UI 层与函数层属**语义错误**，人工审核与执行
    人员按此理解会走错通道（实测影响 993/1715 条用例）。
    """
    method = _get(tp, "method")
    area = _get(tp, "area")
    source = str(_get(tp, "source")).replace("\\", "/")
    category = _get(tp, "category", TPType.NORMAL.value)
    expect = _get(tp, "expect")
    tail = f"，来源文件 {source}" if source else ""
    kind = method_kind(str(method))
    is_ui = layer == VerifyLayer.UI.value

    if is_ui and kind == FType.PAGE.value:
        prepare = f"打开页面：{area}{tail}"
        execute = f"访问 {area}，等待首屏渲染完成并收集控制台错误"
    elif is_ui:
        prepare = f"定位交互点：{area}{tail}"
        execute = f"触发 {area} 的交互（点击／输入），观察界面响应"
    elif kind == FType.API.value:
        prepare = f"构造请求：{method} {area}{tail}"
        execute = f"发送 {method} {area} 请求并捕获响应"
    else:
        prepare = f"准备调用上下文：{area}{tail}"
        execute = f"调用函数 {area}，捕获返回值与异常"

    if category == TPType.ABNORMAL.value:
        assert_desc = (
            "校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏"
            if kind == FType.API.value
            else "校验：函数对非法输入抛出预期异常或返回错误码，且不产生未捕获异常或数据损坏"
        )
    elif category == TPType.SECURITY.value:
        assert_desc = "校验：无凭证/越权访问被拒绝（401/403），且不泄露资源内容"
    elif kind == FType.API.value:
        assert_desc = "校验：响应状态码符合预期，关键业务字段完整"
    elif kind == FType.PAGE.value:
        assert_desc = "校验：页面正常渲染（无白屏／无控制台报错），关键元素可见"
    elif kind == FType.UI.value:
        assert_desc = "校验：交互后界面按预期变化，无报错提示或状态残留"
    else:
        assert_desc = "校验：返回值符合语义，异常分支被正确捕获"

    return [
        {"seq": 1, "type": "前置", "desc": precondition},
        {"seq": 2, "type": "准备", "desc": prepare},
        {"seq": 3, "type": "执行", "desc": execute},
        {"seq": 4, "type": "断言", "desc": assert_desc, "expect": expect},
    ]


def build_case(
    tp: Any,
    fp_row_id: int | None = None,
    *,
    ui_modules: set[str] | None = None,
    strategy: str = LAYER_STRATEGY_UI_FIRST,
    drop_supplement: bool = False,
) -> CaseSpec | None:
    """由一条测试点构建用例规格。

    覆盖角色（UI 优先策略）：
    - UI 层用例恒为 `primary`（UI 是优先验证层）；
    - 接口层用例：在 `ui_first` 策略下，若其所属模块已有 UI 覆盖 → `supplement`
      （接口仅作补充），否则仍为 `primary`（该后端能力 UI 无法覆盖，接口是必要的）；
    - `drop_supplement=True` 时，补充用例直接返回 None（被上层过滤丢弃）。
    """
    category = _get(tp, "category", TPType.NORMAL.value)
    method = str(_get(tp, "method"))
    area = str(_get(tp, "area"))
    source = str(_get(tp, "source")).replace("\\", "/")
    tp_id = str(_get(tp, "tp_id"))
    fp_contract_id = str(_get(tp, "fp_contract_id"))
    expect = str(_get(tp, "expect"))
    title_text = str(_get(tp, "title")) or tp_id
    # 测试点标题通常已自带 `[维度]` 前缀，此处只在缺失时补，避免出现 `[安全] [安全] …`
    prefix = f"[{category}]"
    title = title_text if title_text.startswith(prefix) else f"{prefix} {title_text}"

    is_api, kind = _method_kind(method)
    ctype = FType.API.value if is_api else "e2e"
    # 执行层（接口 / UI）以测试点自带的 verify_layer 为准；缺失时按 method 标记回退推导。
    # 不能再用「是否 HTTP 动词」当判据：后端业务函数（method=FUNC）不是 HTTP 接口，
    # 但它属于**接口层**，早期实现会把它派成 ui_probe → 执行器去拉浏览器打开一个函数。
    layer = str(_get(tp, "verify_layer")) or verify_layer_of_ftype(kind)
    is_ui_layer = layer == VerifyLayer.UI.value
    module = str(_get(tp, "module"))

    # —— 覆盖角色 ——
    if is_ui_layer:
        coverage_role = COVERAGE_ROLE_PRIMARY
    elif strategy == LAYER_STRATEGY_UI_FIRST and module in (ui_modules or set()):
        coverage_role = COVERAGE_ROLE_SUPPLEMENT
    else:
        coverage_role = COVERAGE_ROLE_PRIMARY
    if drop_supplement and coverage_role == COVERAGE_ROLE_SUPPLEMENT:
        return None

    precondition = precondition_of(category, layer)

    steps = [
        {
            "action": "ui_probe" if is_ui_layer else "http_probe",
            "layer": layer,  # 契约「只增不破」：新增可选字段，供下游按执行层分组
            "kind": kind,
            "tp_id": tp_id,
            "fp_id": fp_contract_id,
            "source": source,
            "file": source,  # 兼容字段：与 source 同值，供旧消费方读取
            "method": method,
            "path": area,
            "func": area if kind == FType.BUSINESS.value else None,
            "dimension": _get(tp, "dimension"),
            "expect": expect,
            "coverage_role": coverage_role,  # 契约 Additive：UI 优先覆盖角色
        }
    ]

    return CaseSpec(
        tc_no=tp_id,
        title=title,
        ctype=ctype,
        steps=steps,
        module=module,
        case_type=str(category),
        priority=priority_of(str(category), module),
        precondition=precondition,
        doc_steps=build_doc_steps(tp, precondition, layer),
        tp_id=tp_id,
        fp_contract_id=fp_contract_id,
        fp_row_id=fp_row_id,
        test_type=str(_get(tp, "tag", "全量")),
        coverage_role=coverage_role,
    )


def generate_cases(
    tps: list[Any],
    fp_row_map: dict[str, int] | None = None,
    *,
    ui_modules: set[str] | None = None,
    strategy: str = LAYER_STRATEGY_UI_FIRST,
    drop_supplement: bool = False,
) -> list[CaseSpec]:
    """批量生成：测试点 → 用例，1:1 对应（契约不变）。

    `ui_modules` 为「已有 UI 覆盖的模块集合」，用于判定接口层用例是否仅为补充。
    `drop_supplement=True` 时过滤掉所有补充用例（纯 UI 优先视图）。
    """
    fp_row_map = fp_row_map or {}
    out: list[CaseSpec] = []
    for tp in tps:
        spec = build_case(
            tp,
            fp_row_map.get(str(_get(tp, "fp_contract_id"))),
            ui_modules=ui_modules,
            strategy=strategy,
            drop_supplement=drop_supplement,
        )
        if spec is not None:
            out.append(spec)
    return out


def from_test_point(tp: TestPoint, fp_row_id: int | None = None) -> CaseSpec | None:
    return build_case(tp, fp_row_id)


def coverage_of(cases: list[CaseSpec], tps: list[Any]) -> dict[str, Any]:
    """用例 / 测试点覆盖体检：孤儿为 0 才算达标。"""
    tp_ids = {str(_get(t, "tp_id")) for t in tps}
    case_tps = {c.tp_id for c in cases}
    orphan = sorted(case_tps - tp_ids)
    uncovered = sorted(tp_ids - case_tps)
    return {
        "tp_count": len(tp_ids),
        "case_count": len(cases),
        "orphan_cases": orphan,
        "orphan_count": len(orphan),
        "uncovered_tp": uncovered,
        "uncovered_count": len(uncovered),
    }
