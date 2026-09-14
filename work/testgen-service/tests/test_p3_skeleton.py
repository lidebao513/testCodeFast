"""P3 接入冒烟测试：模块可导入；仍未实现的桩函数按预期抛出异常。

注：`runtime_ui.discover_ui` 已于 M3.1–M3.2 落地（真实实现），其行为测试见
`tests/test_p3_runtime_ui.py`；本文件只保留「模块可导入 + 未实现桩」两类冒烟。
"""

from __future__ import annotations

import pytest

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


def test_executor_stub():
    with pytest.raises(NotImplementedError):
        executor.execute_case(None)
