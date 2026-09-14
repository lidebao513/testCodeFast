"""P3 接入骨架冒烟测试：模块可导入、桩函数按预期抛出 NotImplementedError。"""

from __future__ import annotations

import pytest

from engine import executor, runtime_ui


def test_modules_importable():
    assert runtime_ui.RuntimeUiResult is not None
    assert runtime_ui.UiElement is not None
    assert executor.ExecutionResult is not None
    assert executor.StepResult is not None


def test_runtime_ui_stub():
    with pytest.raises(NotImplementedError):
        runtime_ui.discover_ui()


def test_executor_stub():
    with pytest.raises(NotImplementedError):
        executor.execute_case(None)
