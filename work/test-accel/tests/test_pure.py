#!/usr/bin/env python3
# ============================================================================
# 纯函数单测（tests/ 真实测试层）：为 backend 核心纯逻辑建立可回归的覆盖率地基。
# 这些函数是「执行层派发 / 稳定 ID」等关键不变量，应在全面重写前就被锁定。
# ============================================================================
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_derive_verify_layer_all_ftypes():
    from backend.core.enums import FType, VerifyLayer, derive_verify_layer

    # 接口型来源 → 接口层
    assert derive_verify_layer(FType.API.value) == VerifyLayer.INTERFACE
    assert derive_verify_layer(FType.BUSINESS.value) == VerifyLayer.INTERFACE
    # 前端产物 → UI 层
    assert derive_verify_layer(FType.PAGE.value) == VerifyLayer.UI
    assert derive_verify_layer(FType.UI.value) == VerifyLayer.UI
    assert derive_verify_layer(FType.COMPONENT.value) == VerifyLayer.UI


def test_select_execution_mode_interface_preferred():
    from backend.core.enums import FType, VerifyLayer, select_execution_mode

    # 用户选接口层 → 不回退
    assert (
        select_execution_mode(VerifyLayer.INTERFACE, FType.PAGE.value, True)
        == VerifyLayer.INTERFACE
    )
    assert (
        select_execution_mode(VerifyLayer.INTERFACE, FType.API.value, False)
        == VerifyLayer.INTERFACE
    )


def test_select_execution_mode_ui_fallback():
    from backend.core.enums import FType, VerifyLayer, select_execution_mode

    # UI 偏好 + 接口型来源 → 回退接口
    assert select_execution_mode(VerifyLayer.UI, FType.API.value, True) == VerifyLayer.INTERFACE
    # UI 偏好 + 无浏览器 → 回退接口
    assert select_execution_mode(VerifyLayer.UI, FType.PAGE.value, False) == VerifyLayer.INTERFACE
    # UI 偏好 + UI 可用 + 前端来源 → UI
    assert select_execution_mode(VerifyLayer.UI, FType.PAGE.value, True) == VerifyLayer.UI


def test_verify_layer_of_variants():
    from backend.core.enums import VerifyLayer, verify_layer_of

    # 已注入 verify_layer 字段 → 直接采用
    assert verify_layer_of({"verify_layer": "接口"}) == VerifyLayer.INTERFACE
    assert verify_layer_of({"verify_layer": "UI"}) == VerifyLayer.UI
    # 仅 ftype → 推导
    assert verify_layer_of({"ftype": "api"}) == VerifyLayer.INTERFACE
    # 仅 method(GET) → 推导 api
    assert verify_layer_of({"method": "GET /x"}) == VerifyLayer.INTERFACE
    # 仅 method(PAGE) → 推导 ui
    assert verify_layer_of({"method": "PAGE open"}) == VerifyLayer.UI
    # 无字段 → 默认 business → 接口
    assert verify_layer_of({}) == VerifyLayer.INTERFACE


def test_method_kind():
    from backend.core.enums import FType, method_kind

    assert method_kind("POST /api/x") == FType.API.value
    assert method_kind("get /x") == FType.API.value
    assert method_kind("PAGE open") == FType.PAGE.value
    assert method_kind("UI click") == FType.UI.value
    assert method_kind("do something") == FType.BUSINESS.value
    assert method_kind("") == FType.BUSINESS.value


def test_fp_id_stable():
    from backend.modules.code_analyzer import fp_id_of

    a = fp_id_of("api", "src/app.py", "POST /login")
    b = fp_id_of("api", "src/app.py", "POST /login")
    c = fp_id_of("api", "src/app.py", "GET /login")
    # 同输入 → 同 ID（跨机器/跨次稳定）
    assert a == b
    assert a.startswith("FP-")
    assert len(a) == 11  # FP- + 8 位 md5
    # 不同输入 → 不同 ID
    assert a != c
