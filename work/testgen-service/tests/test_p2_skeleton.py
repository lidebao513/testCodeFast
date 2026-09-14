"""P2 接入骨架冒烟测试：模块可导入、桩函数按预期抛出 NotImplementedError。

本文件只验证「骨架契约」——不依赖外部服务 / LLM / 网络，确保接口与桩落地正确。
"""

from __future__ import annotations

import pytest

from engine import llm_design, prd_ingest


def test_modules_importable():
    assert prd_ingest.PrdDoc is not None
    assert prd_ingest.PrdRequirement is not None
    assert llm_design.DesignOptions is not None
    assert llm_design.DesignResult is not None


def test_prd_format_resolver():
    assert prd_ingest._resolve_format("api.yaml", "auto") == "openapi"
    assert prd_ingest._resolve_format("spec.json", "auto") == "openapi"
    assert prd_ingest._resolve_format("prd.md", "auto") == "markdown"
    assert prd_ingest._resolve_format("x.md", "markdown") == "markdown"


def test_prd_ingest_stub():
    with pytest.raises(NotImplementedError):
        prd_ingest.ingest_prd("x.md")
    with pytest.raises(NotImplementedError):
        prd_ingest.requirements_to_test_points(prd_ingest.PrdDoc("x", "markdown"), [])


def test_llm_design_stub():
    with pytest.raises(NotImplementedError):
        llm_design.design_cases([], [])
