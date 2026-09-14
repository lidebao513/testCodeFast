"""P3 接入冒烟测试：模块可导入 + 契约附加性；未实现部分必须**如实标记**而非静默通过。

注：`runtime_ui.discover_ui` 已于 M3.1–M3.3 落地，`executor.execute_case` 的接口层已于 A3
落地（UI 层仍为桩）。其行为测试分别在 `tests/test_p3_runtime_ui.py` 与
`tests/test_a3_executor.py`；本文件只保留最外层冒烟。
"""

from __future__ import annotations

from core.contracts import CaseSpec
from engine import executor, runtime_ui


def test_modules_importable():
    assert runtime_ui.RuntimeUiResult is not None
    assert runtime_ui.UiElement is not None
    assert runtime_ui.UiPage is not None
    assert executor.ExecutionResult is not None
    assert executor.StepResult is not None


def test_runtime_ui_options_contract_is_additive():
    """P3 新增字段均为「有默认值」的附加项，不破坏既有构造方式。"""
    opts = runtime_ui.RuntimeUiOptions()
    assert opts.mode == "playwright"
    assert opts.login_user == ""
    assert opts.login_password == ""
    assert opts.routes == []
    assert opts.max_pages > 0
    assert opts.degraded is False


def test_executor_ui_layer_is_explicitly_skipped_not_passed():
    """UI 层执行器仍是桩 → 必须如实 skipped 且给出原因，**绝不能**伪装成通过。"""
    case = CaseSpec(
        tc_no="TP-00000001",
        title="[正常] 页面可达",
        ctype="e2e",
        steps=[{"action": "ui_probe", "layer": "UI", "kind": "page", "path": "/pc/tasks"}],
    )
    result = executor.execute_case(case)
    assert result.status == executor.ExecStatus.SKIPPED.value
    assert not result.ok(), "skipped 不得算作通过"
    assert "UI 层执行器待实现" in result.notes[0]
