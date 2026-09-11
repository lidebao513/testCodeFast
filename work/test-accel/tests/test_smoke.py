#!/usr/bin/env python3
# ============================================================================
# 冒烟测试（tests/ 真实测试层，被 pytest + CI 跑）
# 目标：把项目级护栏变成可自动执行的断言，防「优化生成」静默破坏
# ============================================================================
import os
import subprocess
import sys

import pytest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_enums_importable():
    """枚举单源可导入，且关键枚举/函数存在。"""
    from backend.core import enums

    for name in (
        "TPType",
        "Tag",
        "FType",
        "VerifyLayer",
        "ExecStatus",
        "derive_verify_layer",
        "select_execution_mode",
    ):
        assert hasattr(enums, name), f"enums 缺失 {name}"


def test_verify_layer_values():
    """执行层枚举取值稳定，且推导正确。"""
    from backend.core.enums import FType, VerifyLayer, derive_verify_layer

    assert {v.value for v in VerifyLayer} == {"接口", "UI"}
    assert derive_verify_layer(FType.API.value) == VerifyLayer.INTERFACE
    assert derive_verify_layer(FType.PAGE.value) == VerifyLayer.UI


def test_select_execution_mode_fallback():
    """UI 优先但接口型/无浏览器 → 回退接口层。"""
    from backend.core.enums import FType, VerifyLayer, select_execution_mode

    # 接口型，偏好 UI → 回退接口
    assert select_execution_mode(VerifyLayer.UI, FType.API.value, True) == VerifyLayer.INTERFACE
    # page 且 UI 可用 → UI
    assert select_execution_mode(VerifyLayer.UI, FType.PAGE.value, True) == VerifyLayer.UI
    # page 但无浏览器 → 回退接口
    assert select_execution_mode(VerifyLayer.UI, FType.PAGE.value, False) == VerifyLayer.INTERFACE


def test_enum_gate_zero_violation():
    """枚举门禁必须零硬违规（项目不跑偏的核心护栏）。"""
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "check_enums.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"check_enums 非零退出：\n{r.stdout}\n{r.stderr}"


def test_structure_gate_no_error():
    """架构结构门禁必须零 error（warning 允许）。"""
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "check_structure.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"check_structure 存在硬违规：\n{r.stdout}\n{r.stderr}"


def test_core_no_top_layer_import():
    """core 层不得反向依赖上层（防止引擎无法被 skill 独立引用）。"""
    core_dir = os.path.join(ROOT, "backend", "core")
    bad = ("backend.modules", "backend.service", "backend.cli", "backend.main")
    pat = __import__("re").compile(r"(?:from\s+([\w\.]+)|import\s+([\w\.]+))")
    for dp, _, files in os.walk(core_dir):
        if "__pycache__" in dp:
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(dp, fn), encoding="utf-8", errors="ignore") as fh:
                src = fh.read()
            for m in pat.finditer(src):
                mod = (m.group(1) or m.group(2) or "").replace(" ", "")
                assert not any(mod == b or mod.startswith(b + ".") for b in bad), (
                    f"core 禁止依赖 {mod}"
                )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
