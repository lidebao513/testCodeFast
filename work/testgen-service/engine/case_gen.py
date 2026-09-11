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
from core.enums import HTTP_METHODS, FType, MethodMarker, TPType, VerifyLayer


_KIND_BY_MARKER = {
    MethodMarker.PAGE.value: FType.PAGE.value,
    MethodMarker.UI.value: FType.UI.value,
    MethodMarker.FUNC.value: FType.BUSINESS.value,
}


def _get(tp: Any, key: str, default: Any = "") -> Any:
    value = tp.get(key, default) if isinstance(tp, Mapping) else getattr(tp, key, default)
    return default if value is None else value


def _method_kind(method: str) -> tuple[bool, str]:
    """返回 (是否接口类, kind)。"""
    m = (method or "").upper().strip()
    if m in HTTP_METHODS:
        return True, ""
    return False, _KIND_BY_MARKER.get(m, FType.COMPONENT.value)


def build_doc_steps(tp: Any, precondition: str) -> list[dict[str, Any]]:
    """人类可读四步：前置 → 准备 → 执行 → 断言。"""
    method = _get(tp, "method")
    area = _get(tp, "area")
    source = str(_get(tp, "source")).replace("\\", "/")
    category = _get(tp, "category", TPType.NORMAL.value)
    expect = _get(tp, "expect")
    if category == TPType.ABNORMAL.value:
        assert_desc = (
            "校验：接口对非法/边界输入返回预期错误（4xx/5xx），且不产生未捕获异常或数据损坏"
        )
    elif category == TPType.SECURITY.value:
        assert_desc = "校验：无凭证/越权访问被拒绝（401/403），且不泄露资源内容"
    else:
        assert_desc = "校验：响应状态码符合预期，关键业务字段完整"
    return [
        {"seq": 1, "type": "前置", "desc": precondition},
        {
            "seq": 2,
            "type": "准备",
            "desc": f"构造请求：{method} {area}" + (f"，来源文件 {source}" if source else ""),
        },
        {"seq": 3, "type": "执行", "desc": f"发送 {method} {area} 请求并捕获响应"},
        {"seq": 4, "type": "断言", "desc": assert_desc, "expect": expect},
    ]


def build_case(tp: Any, fp_row_id: int | None = None) -> CaseSpec:
    """由一条测试点构建用例规格。"""
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
    precondition = precondition_of(category)

    # 执行层（接口 / UI）以测试点自带的 verify_layer 为准；缺失时按 method 标记回退推导。
    # 不能再用「是否 HTTP 动词」当判据：后端业务函数（method=FUNC）不是 HTTP 接口，
    # 但它属于**接口层**，早期实现会把它派成 ui_probe → 执行器去拉浏览器打开一个函数。
    layer = str(_get(tp, "verify_layer")) or verify_layer_of_ftype(kind or FType.API.value)
    is_ui_layer = layer == VerifyLayer.UI.value

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
        }
    ]

    return CaseSpec(
        tc_no=tp_id,
        title=title,
        ctype=ctype,
        steps=steps,
        module=str(_get(tp, "module")),
        case_type=str(category),
        priority=priority_of(str(category), str(_get(tp, "module"))),
        precondition=precondition,
        doc_steps=build_doc_steps(tp, precondition),
        tp_id=tp_id,
        fp_contract_id=fp_contract_id,
        fp_row_id=fp_row_id,
        test_type=str(_get(tp, "tag", "全量")),
    )


def generate_cases(
    tps: list[Any],
    fp_row_map: dict[str, int] | None = None,
) -> list[CaseSpec]:
    """批量生成：测试点 → 用例，1:1 对应（契约不变）。"""
    fp_row_map = fp_row_map or {}
    return [build_case(tp, fp_row_map.get(str(_get(tp, "fp_contract_id")))) for tp in tps]


def from_test_point(tp: TestPoint, fp_row_id: int | None = None) -> CaseSpec:
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
