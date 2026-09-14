"""引擎 · 模块十一（P3）：用例执行器（接口探活 / 浏览器交互）。

设计定位：把生成的用例真正跑起来。接口层用例走 requests 探活 + 结构/契约断言
（与 legacy 的 executor 思路一致）；UI 层用例走 Playwright 真实交互。执行结果
回填 cases.last_result 与 runs。

本文件为**接入骨架**：仅定义数据契约与接口桩；requests / Playwright 在运行时惰性导入。
依赖方向严格向下（只 import core），不感知 service / cli。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.contracts import CaseSpec
from core.enums import ExecStatus


@dataclass
class ExecutorOptions:
    """执行器选项。"""

    base_url: str = ""
    auth_token: str = ""  # 来自环境变量，不入库
    headless: bool = True
    timeout: int = 30


@dataclass
class StepResult:
    """单步执行结果。"""

    seq: int
    ok: bool
    detail: str = ""


@dataclass
class ExecutionResult:
    """一次用例执行结果。"""

    tc_no: str = ""
    status: str = ExecStatus.SKIPPED.value
    step_results: list[StepResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def execute_case(case: CaseSpec, options: ExecutorOptions | None = None) -> ExecutionResult:
    """执行单条用例（按 steps[0].layer 选择接口 / UI 通道）。

    骨架桩：后续实现分派 requests / Playwright；接口层做探活 + 结构断言，
    UI 层做真实浏览器交互与断言。
    """
    raise NotImplementedError("executor.execute_case 尚未实现（P3 接入骨架）")
