"""引擎 · 模块九（P2）：LLM 用例设计（在语义增强之外叠加用例生成）。

设计定位：复用 semantic_enrich 的 LLMClient 与防胡说校验层，但目标从
「补充测试点」升级为「基于功能点 + PRD 上下文设计可执行用例」。同样受
LLM 开关与 Prompt 注入防护约束，且生成的用例不得臆造代码中不存在的接口。

本文件为**接入骨架**：仅定义数据契约与接口桩；OpenAI 依赖在真正调用时惰性导入。
依赖方向严格向下（只 import core），不感知 service / cli。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.contracts import CaseSpec, FunctionalPoint, TestPoint


@dataclass
class DesignOptions:
    """LLM 用例设计选项。"""

    enabled: bool = False
    provider: str = "qwen"
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    timeout: int = 60
    max_cases_per_fp: int = 3


@dataclass
class DesignResult:
    """设计结果。"""

    cases: list[CaseSpec] = field(default_factory=list)
    added: list[CaseSpec] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def design_cases(
    fps: list[FunctionalPoint],
    tps: list[TestPoint],
    prd: Any | None = None,
    options: DesignOptions | None = None,
) -> DesignResult:
    """基于功能点 + 测试点 + 可选 PRD 上下文，用 LLM 设计用例。

    骨架桩：后续实现复用 semantic_enrich.LLMClient 发起请求，并经
    validate_candidates 校验层过滤臆造条目。
    """
    raise NotImplementedError("llm_design.design_cases 尚未实现（P2 接入骨架）")
