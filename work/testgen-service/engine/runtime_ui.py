"""引擎 · 模块十（P3）：运行时浏览器 UI 发现。

设计定位：在「代码静态分析得到的 UI 功能点」之外，提供运行时验证通道——
用 Playwright 打开被测环境地址（用户提供 + 凭证经 .env 注入），真实渲染页面、
抓取可交互元素、记录控制台错误，反向补全 / 校验 UI 测试点。

本文件为**接入骨架**：仅定义数据契约与接口桩；Playwright 依赖在运行时惰性导入。
依赖方向严格向下（只 import core），不感知 service / cli。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.enums import RUNTIME_UI_MODE_CHOICES, RUNTIME_UI_PLAYWRIGHT


@dataclass
class RuntimeUiOptions:
    """运行时 UI 发现选项。"""

    mode: str = RUNTIME_UI_PLAYWRIGHT
    headless: bool = True
    base_url: str = ""
    auth_token: str = ""  # 来自环境变量，不入库
    timeout: int = 30


@dataclass
class UiElement:
    """一个被发现的 UI 元素 / 交互点。"""

    selector: str
    kind: str = ""
    text: str = ""
    visible: bool = False


@dataclass
class RuntimeUiResult:
    """运行时 UI 发现结果。"""

    base_url: str = ""
    elements: list[UiElement] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def discover_ui(options: RuntimeUiOptions | None = None) -> RuntimeUiResult:
    """打开被测环境，抓取可交互元素与控制台错误。

    骨架桩：后续实现惰性导入 Playwright 并驱动浏览器；凭证来自 options.auth_token
    （运行时由环境变量注入，不落库）。
    """
    opts = options or RuntimeUiOptions()
    if opts.mode not in RUNTIME_UI_MODE_CHOICES:
        raise ValueError(f"未知的运行时 UI 发现模式：{opts.mode!r}，允许 {RUNTIME_UI_MODE_CHOICES}")
    raise NotImplementedError("runtime_ui.discover_ui 尚未实现（P3 接入骨架）")
