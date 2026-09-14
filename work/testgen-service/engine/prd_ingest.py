"""引擎 · 模块八（P2）：PRD 通道（需求文档 → 结构化需求 → 测试点候选）。

设计定位：在「代码静态分析」之外，提供第二条来源通道——把 PRD / 接口文档 /
OpenAPI 规格解析为结构化需求，与代码提取出的功能点做对齐，弥补「代码里看不出
业务意图」的盲区（见 qa-test-points 技能 §十一）。

本文件为**接入骨架**：仅定义数据契约与接口桩，真实解析在后续实现阶段填充。
依赖方向严格向下（只 import core），不感知 service / cli。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.enums import PRD_FORMAT_AUTO, PRD_FORMAT_CHOICES
from core.errors import ConfigError


@dataclass
class PrdRequirement:
    """一条结构化需求。"""

    rid: str
    title: str
    description: str = ""
    source: str = ""  # 来源文件 / 章节
    endpoints: list[str] = field(default_factory=list)  # 关联接口（path 或 name）
    tags: list[str] = field(default_factory=list)


@dataclass
class PrdDoc:
    """一份 PRD 的解析结果。"""

    source: str
    fmt: str
    requirements: list[PrdRequirement] = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "fmt": self.fmt,
            "requirements": [asdict(r) for r in self.requirements],
            "raw": self.raw,
        }


@dataclass
class PrdIngestOptions:
    """PRD 解析选项。"""

    fmt: str = PRD_FORMAT_AUTO
    encoding: str = "utf-8"


def _resolve_format(source: str, fmt: str) -> str:
    """按显式 fmt 或文件扩展名推断 PRD 格式；非法值抛 ConfigError。"""
    if fmt != PRD_FORMAT_AUTO:
        if fmt not in PRD_FORMAT_CHOICES:
            raise ConfigError(f"PRD 格式非法：{fmt!r}，允许 {PRD_FORMAT_CHOICES}")
        return fmt
    lowered = source.lower()
    if lowered.endswith(".json") or lowered.endswith(".yaml") or lowered.endswith(".yml"):
        return "openapi"
    return "markdown"


def ingest_prd(source: str, options: PrdIngestOptions | None = None) -> PrdDoc:
    """解析 PRD 文档为结构化需求。

    骨架桩：后续实现按 `_resolve_format` 分派 markdown / openapi 解析器，
    产出 PrdRequirement 列表。
    """
    raise NotImplementedError("prd_ingest.ingest_prd 尚未实现（P2 接入骨架）")


def requirements_to_test_points(prd: PrdDoc, fps: list[Any]) -> list[Any]:
    """把结构化需求对齐到功能点，产出补充测试点候选。

    骨架桩：后续实现做「需求 ↔ 功能点」映射与去重（需求里提到的接口若已在
    代码功能点中存在，则派生测试点；否则标记为待人工确认）。
    """
    raise NotImplementedError("prd_ingest.requirements_to_test_points 尚未实现（P2 接入骨架）")
