"""引擎 · 模块十（P3）：运行时浏览器 UI 发现。

设计定位：在「代码静态分析得到的 UI 功能点」之外，提供运行时验证通道——
用 Playwright 打开被测环境地址（用户提供 + 凭证经 .env 注入），真实渲染页面、
抓取可交互元素、记录控制台错误，反向补全 / 校验 UI 测试点。

依赖方向严格向下（只 import core），不感知 service / cli。
Playwright 采用**惰性导入**：未安装时不影响主链路（默认关闭），
由 `_has_playwright()` 探测，`discover_ui` 在缺失时给出可执行的安装指引。

里程碑：
- M3.1 配置与凭证模型 + 惰性导入探测；
- M3.2 表单登录 + 单页抓取 + 路由来源优先级；
- M3.3 三字段登录（账号 / 密码 / 动态口令）+ SPA 菜单点击路由发现 + 受保护页遍历；
- M3.4 `to_functional_points` 把发现结果转成 `FunctionalPoint`，并由 pipeline
  与静态功能点**合并去重**后参与测试点展开与用例生成。

凭证红线（见 `P3_UI生成_详细设计.md` §4.2）：
密码/令牌/动态口令只从环境变量读取，**不进日志、不进产物、不进数据库**——本模块所有
日志调用点均不携带凭证字段，结果 note 也不回显密码与动态口令。

⚠️ SPA 实战教训（一个真实 React SPA 实测，三条都会让菜单发现静默得到 0 条）：
1. **菜单在 SPA 外壳里跨路由常驻**——不要「每项重新打开页面」再抓句柄；单会话内点击、
   按「文本 → 索引」重新定位即可（重开还会撞上首屏异步挂载，句柄为空）。
2. **不要用很短的预算等导航挂载**：首批菜单常要等后端接口返回才渲染，预算太紧会误判
   「本页没有导航」从而直接放弃。
3. **不要把所有菜单的 `href` 当成真实路由**：SPA 里 `href` 可能是占位值或全部同值，
   只有真实点击才驱动路由库跳转——故取路由必须**点击优先**，`href` 仅作兜底。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from core.contracts import FunctionalPoint, fp_id_of
from core.enums import RUNTIME_UI_MODE_CHOICES, RUNTIME_UI_PLAYWRIGHT, FType
from core.errors import EngineError
from core.log import get_logger, log_extra


log = get_logger(__name__)


# ============================================================================
# 常量（选择器与上限集中于此，便于后续配置化）
# ============================================================================
# 导航类元素：登录后才可见的权限菜单是运行时发现相对静态分析的核心增量。
# 重要：SPA（React/Vue + antd 等）菜单也常是带类名的 div/li，故同时覆盖
# 「语义标签」与「常见菜单类名」，不假设一定是 `<a>`。
_NAV_SELECTOR = (
    'nav a, aside a, [role="menuitem"], [role="tab"], '
    ".menu a, .sidebar a, header a, "
    '[class*="menu-item"], [class*="menuItem"], [class*="nav-item"], [class*="navItem"], '
    '[class*="nav"] [class*="-item"], [class*="sidebar"] [class*="-item"], '
    '[class*="menu"] [class*="-item"]'
)
# 按钮类元素：语义 button 之外，还要覆盖 role=button 与常见 btn 类名
_BUTTON_SELECTOR = 'button, [role="button"], input[type=submit], [class*="btn"]'
# 表单控件：input / select / textarea / form
# 以及富文本编辑区（SPA 常用 contenteditable 代替 input 作输入框）
_FORM_SELECTOR = "form, input, select, textarea, [contenteditable='true']"
# 一次性取回导航项文本（用于 SPA 跳转后按文本重新定位，避免逐元素往返）
_NAV_LABELS_JS = (
    "els => els.map(e => (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40))"
)

# 单页元素上限（防爆：超长列表页可达数千个元素）
MAX_ELEMENTS_PER_PAGE = 200
# 首页链接爬取上限
MAX_HOME_LINKS = 300
# 单页控制台错误上限
MAX_CONSOLE_ERRORS_PER_PAGE = 20
# 控制台错误全站累积上限（防日志/结果爆炸）
MAX_CONSOLE_ERRORS_TOTAL = 500
# SPA 路由切换后的静默等待（毫秒）
SPA_SETTLE_MS = 900
# 进入新页面后等「网络静默」的上限（毫秒）。
# SPA 普遍有长轮询/心跳，`networkidle` 往往**永远不满足**；若照配置超时（几十秒）等，
# 遍历十几个路由就会拖到数分钟。这里只需要「首屏渲染差不多完成」，故给一个短预算。
SETTLE_AFTER_GOTO_MS = 2500
# 等待 SPA 挂载导航菜单的上限（毫秒）：首批菜单常要等接口返回，预算不能太紧
NAV_READY_TIMEOUT_MS = 12000

# 静态资源扩展名：这些「路径」是文件下载 / 前端产物，不是可测页面。
# 真实环境里首页「下载客户端」链接（/downloads/xxx-win.zip）也被 `nav a` 命中，
# 且会被 SPA 兜底路由渲染成与首页同构的假页面，若不去掉就会凭空多出 1 个「页面功能点」。
_STATIC_ASSET_EXTS = (
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".css",
    ".js",
    ".mjs",
    ".map",
    ".json",
    ".xml",
    ".txt",
    ".csv",
    ".mp4",
    ".mp3",
    ".woff",
    ".woff2",
    ".ttf",
)

# 登录选择器（按优先级排列；命中第一个即用）
# 密码框：type=password 之外，SPA（antd / Tailwind 自定义组件）常把密码框做成
# `type=text` + 遮罩，故补 placeholder 兜底（实测目标站密码框占位即「密码」）
_PASSWORD_SELECTORS = (
    "input[type=password]",
    'input[name*="pass" i]',
    'input[placeholder*="密码"]',
)
_USER_SELECTORS = (
    'input[placeholder*="邮箱"]',
    'input[placeholder*="账号"]',
    'input[placeholder*="邮箱账号"]',
    "input[type=email]",
    'input[name*="user" i]',
    'input[name*="account" i]',
    'input[name*="mobile" i]',
    'input[name*="email" i]',
    "input[type=text]",
    "input:not([type])",
)
# 动态口令 / 一次性验证码 / 短信码（福享 Agent 登录页为「邮箱账号 + 密码 + 动态口令（6位）」）
_OTP_SELECTORS = (
    'input[placeholder*="动态"]',
    'input[placeholder*="口令"]',
    'input[placeholder*="验证码"]',
    'input[placeholder*="短信"]',
    'input[name*="otp" i]',
    'input[name*="captcha" i]',
    'input[name*="verify" i]',
)
_SUBMIT_SELECTORS = (
    "button[type=submit]",
    "input[type=submit]",
    'button:has-text("登 录")',
    'button:has-text("登录")',
    'button:has-text("登陆")',
    'button:has-text("Login")',
    'button:has-text("Sign in")',
    ".login-button",
)

_INSTALL_HINT = (
    "运行时 UI 发现需要 Playwright。请在项目 venv 中执行："
    "python -m pip install playwright && python -m playwright install chromium"
    "（沙箱内无法下载内核时可改用系统浏览器：设 PLAYWRIGHT_CHANNEL=msedge）"
)


# ============================================================================
# 数据契约（只增不破）
# ============================================================================
@dataclass
class RuntimeUiOptions:
    """运行时 UI 发现选项。"""

    mode: str = RUNTIME_UI_PLAYWRIGHT
    headless: bool = True
    base_url: str = ""
    auth_token: str = ""  # 来自环境变量，不入库
    timeout: int = 30
    # --- M3.2 新增（Additive）---
    channel: str = ""  # ""=自带 chromium；"msedge"/"chrome"=复用系统浏览器
    login_user: str = ""  # 表单登录账号
    login_password: str = ""  # 表单登录密码（不入库 / 不日志）
    login_url: str = ""  # 登录页地址；为空回退到 base_url
    routes: list[str] = field(default_factory=list)  # 显式路由清单（优先级最高）
    max_pages: int = 60  # 遍历页面上限（防爆）
    degraded: bool = False  # 是否降级为 requests 抓取（M3.5 落地，占位）
    # --- M3.3 新增（Additive）---
    login_otp: str = ""  # 动态口令 / 一次性验证码（不入库 / 不日志）
    discover_by_menu: bool = True  # 是否靠点菜单发现 SPA 路由（无正确 href 时的唯一途径）


@dataclass
class UiElement:
    """一个被发现的 UI 元素 / 交互点。"""

    selector: str
    kind: str = ""
    text: str = ""
    visible: bool = False


@dataclass
class UiPage:
    """一个被发现的可达页面。"""

    url: str
    path: str
    title: str = ""
    reachable: bool = True
    console_errors: list[str] = field(default_factory=list)
    elements: list[UiElement] = field(default_factory=list)


@dataclass
class RuntimeUiResult:
    """运行时 UI 发现结果。"""

    base_url: str = ""
    elements: list[UiElement] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    pages: list[UiPage] = field(default_factory=list)
    degraded: bool = False
    logged_in: bool = False  # 是否执行了表单登录并成功（匿名访问为 False）
    # --- M3.3 新增（Additive）---
    discovered_routes: list[str] = field(default_factory=list)  # 菜单点击发现的路由

    def reachable_pages(self) -> list[UiPage]:
        """可达页面（`reachable=True`）。"""
        return [p for p in self.pages if p.reachable]


@dataclass
class _Session:
    """一次浏览器会话（页面 + 其上下文）。打包传参，避免函数参数过长。"""

    page: Any
    context: Any


@dataclass
class _MenuProbe:
    """菜单点击探测的输入（参数打包，兼顾可读性与 lint 的参数上限）。"""

    session: _Session
    options: RuntimeUiOptions
    start_url: str
    start_route: str
    labels: list[str]


# ============================================================================
# 可用性探测与配置映射（M3.1）
# ============================================================================
def _has_playwright() -> bool:
    """探测 Playwright 是否可用（决定真实浏览器通道 / 后续降级路径）。"""
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def options_from_settings(settings: Any) -> RuntimeUiOptions:
    """从 `core.config.Settings` 构造选项（凭证只在此处做一次搬运，不落任何产物）。"""
    return RuntimeUiOptions(
        headless=bool(settings.playwright_headless),
        base_url=str(settings.runtime_base_url or ""),
        auth_token=str(settings.runtime_auth_token or ""),
        timeout=int(settings.runtime_ui_timeout),
        channel=str(settings.playwright_channel or ""),
        login_user=str(settings.runtime_login_user or ""),
        login_password=str(settings.runtime_login_password or ""),
        login_otp=str(getattr(settings, "runtime_login_otp", "") or ""),
        login_url=str(settings.runtime_login_url or ""),
        routes=list(settings.runtime_routes or []),
        max_pages=int(settings.runtime_max_pages),
    )


# ============================================================================
# 路由解析（纯函数，便于单测）
# ============================================================================
def _origin(url: str) -> str:
    """取 URL 的源（scheme://netloc），用于同源判定。"""
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.scheme else ""


def _looks_like_asset(path: str) -> bool:
    """路径末段是否像静态资源（.zip/.pdf/.png...）——是则不是可测页面。"""
    name = (path or "").rsplit("/", 1)[-1].lower()
    return any(name.endswith(ext) for ext in _STATIC_ASSET_EXTS)


def _normalize_route(raw: str, base_url: str) -> str | None:
    """把一条候选路由规范化为同源路径；非同源 / 伪协议 / 静态资源返回 None。"""
    item = (raw or "").strip()
    if not item or item.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None
    parts = urlparse(urljoin(base_url, item))
    if parts.scheme not in ("http", "https"):
        return None
    if _origin(base_url) and f"{parts.scheme}://{parts.netloc}" != _origin(base_url):
        return None  # 外链一律跳过
    path = parts.path or "/"
    if _looks_like_asset(path):
        return None  # 下载 / 静态产物不是页面
    return f"{path}?{parts.query}" if parts.query else path


def _resolve_routes(
    options: RuntimeUiOptions,
    static_paths: list[str] | None = None,
    discovered_links: list[str] | None = None,
    menu_paths: list[str] | None = None,
) -> list[str]:
    """路由清单，按优先级合并去重后截断到上限。

    优先级（M3.3 起四档）：显式 routes > **菜单点击发现** > 静态 page 功能点路径 > 首页可点链接。

    「菜单点击发现」插在静态路径之前：它是**真实点出来的**登录后路由，比静态代码里的
    路径声明更贴近线上实际可达面（SPA 常按权限动态拼路由，静态代码看不到）。
    """
    merged: list[str] = []
    seen: set[str] = set()
    limit = max(1, int(options.max_pages))
    groups = (options.routes, menu_paths or [], static_paths or [], discovered_links or [])
    for group in groups:
        for raw in group:
            path = _normalize_route(raw, options.base_url)
            if path is None or path in seen:
                continue
            seen.add(path)
            merged.append(path)
            if len(merged) >= limit:
                return merged
    return merged


# ============================================================================
# 页面操作（M3.2；page 用 Any 标注——Playwright 未安装时不应触发导入）
# ============================================================================
@dataclass
class _ConsoleSink:
    """按顺序累积控制台错误，支持「从某个位置起的新增条目」切片。"""

    entries: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        if len(self.entries) < MAX_CONSOLE_ERRORS_TOTAL:
            self.entries.append(message)

    def since(self, mark: int) -> list[str]:
        return self.entries[mark : mark + MAX_CONSOLE_ERRORS_PER_PAGE]


def _timeout_ms(options: RuntimeUiOptions) -> int:
    """超时（秒）→ 毫秒（至少 1ms）。"""
    return max(1, int(options.timeout)) * 1000


def _safe_url(page: Any) -> str:
    try:
        return str(page.url or "")
    except Exception:  # 页面已崩溃时取值失败属正常，不能因此中断发现
        return ""


def _route_of(page: Any) -> str:
    """当前页面路由（path[?query]），与 `_normalize_route` 输出同构。"""
    parts = urlparse(_safe_url(page))
    path = parts.path or "/"
    return f"{path}?{parts.query}" if parts.query else path


def _attach_listeners(page: Any, sink: _ConsoleSink) -> None:
    """注册控制台错误与未捕获异常的监听（只进结果，不落日志）。"""

    def _on_console(msg: Any) -> None:
        try:
            if str(getattr(msg, "type", "")) == "error":
                sink.add(f"[console] {str(getattr(msg, 'text', ''))[:300]}")
        except Exception:  # 监听回调里的异常不能反噬主流程
            return

    def _on_pageerror(exc: Any) -> None:
        try:
            sink.add(f"[pageerror] {str(exc)[:300]}")
        except Exception:
            return

    page.on("console", _on_console)
    page.on("pageerror", _on_pageerror)


def _first_match(page: Any, selectors: tuple[str, ...]) -> Any:
    """按优先级返回第一个命中的元素句柄（未命中返回 None）。"""
    for sel in selectors:
        try:
            handle = page.query_selector(sel)
        except Exception:  # 单个选择器语法/状态异常不影响继续尝试
            continue
        if handle is not None:
            return handle
    return None


# ============================================================================
# 登录（M3.2 两字段 → M3.3 三字段 + 可选二次验证）
# ============================================================================
def _fill_otp_if_present(page: Any, options: RuntimeUiOptions) -> bool:
    """若配置了动态口令且页面存在口令输入框则填入；返回是否填入。"""
    if not options.login_otp:
        return False
    otp = _first_match(page, _OTP_SELECTORS)
    if otp is None:
        return False
    try:
        otp.fill(options.login_otp)
    except Exception:
        return False
    return True


def _click_submit(page: Any, submit: Any, options: RuntimeUiOptions) -> None:
    try:
        submit.click()
        page.wait_for_load_state("networkidle", timeout=_timeout_ms(options))
    except Exception as exc:  # 提交过程任何失败都归为登录失败
        raise EngineError(f"登录失败：提交登录表单出错（{exc}）") from exc


def _maybe_submit_otp(page: Any, options: RuntimeUiOptions, result: RuntimeUiResult) -> None:
    """二次验证兜底：部分系统是「账号密码 → 下一步 → 动态口令」的两屏流程。

    仅在「首屏没有口令框」且「首屏提交后仍停留登录页且出现口令框」时触发。
    """
    if not options.login_otp or _first_match(page, _PASSWORD_SELECTORS) is None:
        return
    otp = _first_match(page, _OTP_SELECTORS)
    submit = _first_match(page, _SUBMIT_SELECTORS)
    if otp is None or submit is None:
        return
    try:
        otp.fill(options.login_otp)
        submit.click()
        page.wait_for_load_state("networkidle", timeout=_timeout_ms(options))
        result.notes.append("已执行二次验证（动态口令，取值不记录）")
    except Exception:  # 二次提交失败由调用方的「仍在登录页」判定统一兜底
        return


def _wait_login_ready(page: Any, options: RuntimeUiOptions) -> None:
    """等登录表单渲染完成再判定。

    SPA 首屏是客户端异步渲染：`goto(domcontentloaded)` 返回时表单往往还不存在，
    直接查控件会把登录页误判成「公开页」而跳过登录（实测目标站即如此）。
    这里只等「出现任意 input/form」，**不等 networkidle**——登录页常有长轮询/心跳，
    可能永远不 idle。
    """
    try:
        page.wait_for_selector("input, form", timeout=_timeout_ms(options))
    except Exception:  # 超时即认为确实没有登录表单（公开页）
        return


def _login(page: Any, options: RuntimeUiOptions, result: RuntimeUiResult) -> bool:
    """检测登录表单并提交；无表单则视为已登录 / 匿名可访问。

    返回 True 表示执行了表单登录并成功；False 表示未执行登录（无凭证或无表单）。
    失败一律抛 `EngineError`（分类提示），**绝不回显密码 / 动态口令**。
    """
    if not (options.login_user and options.login_password):
        result.notes.append("未提供账号密码：按匿名访问处理（仅公开页可见）")
        return False

    target = options.login_url or options.base_url
    try:
        page.goto(target, wait_until="domcontentloaded", timeout=_timeout_ms(options))
    except Exception as exc:  # 打开登录页失败即登录失败
        raise EngineError(f"登录失败：无法打开登录页 {target}（{exc}）") from exc

    _wait_login_ready(page, options)
    pwd = _first_match(page, _PASSWORD_SELECTORS)
    if pwd is None:
        result.notes.append(
            f"登录页未发现密码输入框（{target}）：视为已登录 / 公开页，跳过表单登录"
        )
        return False

    user = _first_match(page, _USER_SELECTORS)
    submit = _first_match(page, _SUBMIT_SELECTORS)
    if user is None or submit is None:
        raise EngineError(
            "登录失败：未定位到账号输入框或提交按钮，"
            "请确认登录页地址（RUNTIME_LOGIN_URL）或页面选择器"
        )

    before_url = _safe_url(page)
    try:
        user.fill(options.login_user)
        pwd.fill(options.login_password)
    except Exception as exc:  # 填值失败归为登录失败
        raise EngineError(f"登录失败：无法填入账号密码（{exc}）") from exc

    otp_filled_first = _fill_otp_if_present(page, options)
    _click_submit(page, submit, options)
    if not otp_filled_first:
        _maybe_submit_otp(page, options, result)

    if _first_match(page, _PASSWORD_SELECTORS) is not None:
        raise EngineError(
            "登录失败：提交后仍停留在登录页，请核对账号密码 / 动态口令是否正确、"
            "或被测系统是否存在图片验证码 / 风控"
        )
    result.notes.append(
        f"表单登录成功（账号 {options.login_user}，密码与动态口令均不记录）；"
        f"跳转 {before_url} → {_safe_url(page)}"
    )
    return True


def _apply_token(context: Any, options: RuntimeUiOptions, result: RuntimeUiResult) -> None:
    """令牌型鉴权：以自定义 Header 注入（取值不记录）。"""
    if not options.auth_token:
        return
    try:
        context.set_extra_http_headers({"Authorization": f"Bearer {options.auth_token}"})
    except Exception as exc:  # 注入失败降级为继续以匿名访问
        result.notes.append(f"令牌注入失败，已按匿名继续（{exc}）")
        return
    result.notes.append("已注入令牌鉴权头（Authorization: Bearer ***）")


# ============================================================================
# SPA 菜单点击路由发现（M3.3）
# ============================================================================
def _nav_labels(page: Any) -> list[str]:
    """当前页导航项的文本清单（一次 JS 取回；用于 SPA 跳转后按文本重新定位）。"""
    try:
        raw = page.eval_on_selector_all(_NAV_SELECTOR, _NAV_LABELS_JS)
    except Exception:
        return []
    return [str(t) for t in raw] if isinstance(raw, list) else []


def _wait_nav_ready(page: Any, options: RuntimeUiOptions) -> None:
    """等 SPA 把导航菜单挂载出来。

    `goto(domcontentloaded)` 返回时 React/Vue 常尚未渲染；更关键的是**首批菜单往往要等
    后端接口返回**才出现，故预算不能给太紧（给太紧会误判「本页没有导航」→ 静默 0 条）。
    """
    budget = min(_timeout_ms(options), NAV_READY_TIMEOUT_MS)
    try:
        page.wait_for_selector(_NAV_SELECTOR, timeout=budget)
    except Exception:  # 超时即认定该页确实没有导航区
        return


def _return_to(page: Any, url: str, options: RuntimeUiOptions) -> bool:
    """回到起点页并等导航渲染完（仅在需要「恢复」时调用）。"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=_timeout_ms(options))
    except Exception:
        return False
    _wait_nav_ready(page, options)
    return True


def _nav_handles(page: Any) -> list[Any]:
    """当前页的导航项句柄（失败返回空表）。"""
    try:
        return list(page.query_selector_all(_NAV_SELECTOR))
    except Exception:
        return []


def _locate_nav(page: Any, label: str, idx: int) -> Any:
    """在当前 DOM 里定位导航项：优先按文本匹配，退回按索引（SPA 跳转后元素会重建）。"""
    handles = _nav_handles(page)
    if not handles:
        return None
    if label:
        current = _nav_labels(page)
        if label in current and current.index(label) < len(handles):
            return handles[current.index(label)]
    return handles[idx] if idx < len(handles) else None


def _menu_href_route(handle: Any, base_url: str) -> str:
    """菜单项 `href` 指向的路由（兜底用：SPA 里它可能是占位值，不能当主依据）。"""
    try:
        href = handle.get_attribute("href")
    except Exception:
        return ""
    if not href:
        return ""
    return _normalize_route(str(href), base_url) or ""


def _click_and_read_route(page: Any, handle: Any, options: RuntimeUiOptions) -> str:
    """点击一个导航项，等 URL 变化后读回路由（未变化返回空串）。"""
    before = _route_of(page)
    try:
        if not handle.is_visible():
            return ""
        handle.click(timeout=_timeout_ms(options), no_wait_after=True)
    except Exception:  # 单个菜单项点不动不影响其它项（交给 href 兜底）
        return ""
    try:
        page.wait_for_function(
            "prev => location.pathname + location.search !== prev",
            arg=before,
            timeout=SPA_SETTLE_MS + 2000,
        )
    except Exception:  # 未变化（可能是当前页 / 新开标签）→ 交给调用方兜底
        pass
    after = _route_of(page)
    return "" if after == before else after


def _popup_route(popups: list[Any], options: RuntimeUiOptions) -> str:
    """若点击新开了标签页，从弹出页读路由。"""
    for popup in popups:
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=_timeout_ms(options))
            route = _route_of(popup)
        except Exception:
            continue
        if route:
            return route
    return ""


def _route_of_nav_item(page: Any, handle: Any, options: RuntimeUiOptions, popups: list[Any]) -> str:
    """取一个导航项指向的路由。

    顺序：**先真实点击**——SPA 的 `href` 常是占位符、或所有菜单项写成同一个值，
    此时只有点击才会驱动路由库 `pushState` 真正跳转；点击未产生 URL 变化时再退回读
    `href`，最后兜底新标签页。
    """
    popups.clear()
    route = _click_and_read_route(page, handle, options)
    if route:
        return route
    route = _menu_href_route(handle, options.base_url)
    if route:
        return route
    if popups:
        route = _popup_route(popups, options)
    return route


def _probe_menu_routes(probe: _MenuProbe) -> list[str]:
    """**单会话**逐个导航项探测路由（不逐项重新打开页面）。

    真实环境实测：菜单在 SPA 外壳里跨路由常驻，单会话点击 + 按「文本 → 索引」重新定位
    即可；逐项 `goto` 重开不仅慢，还会撞上首屏异步挂载导致句柄为空、静默丢掉全部路由。
    """
    page = probe.session.page
    popups: list[Any] = []

    def _on_page(new_page: Any) -> None:
        popups.append(new_page)

    try:
        probe.session.context.on("page", _on_page)
    except Exception:  # 监听注册失败不影响主流程（只是拿不到新标签页路由）
        pass

    found: list[str] = []
    seen: set[str] = set()
    limit = max(1, int(probe.options.max_pages))
    try:
        for idx, label in enumerate(probe.labels[:limit]):
            handle = _locate_nav(page, label, idx)
            if handle is None:  # 导航被跳转带走了 → 回起点重试一次
                if not _return_to(page, probe.start_url, probe.options):
                    break
                handle = _locate_nav(page, label, idx)
            if handle is None:
                continue
            raw = _route_of_nav_item(page, handle, probe.options, popups)
            route = _normalize_route(raw, probe.options.base_url)
            if route and route != probe.start_route and route not in seen:
                seen.add(route)
                found.append(route)
    finally:
        try:
            probe.session.context.remove_listener("page", _on_page)
        except Exception:
            pass
        _close_all(*popups)
    return found


def _discover_menu_routes(
    page: Any,
    context: Any,
    options: RuntimeUiOptions,
    result: RuntimeUiResult,
) -> list[str]:
    """SPA 路由发现：逐一点击导航项，记录 URL 变化。

    点击本身不计入结果元素，只用于发现路由；收尾回起点供后续抓取落地页。
    """
    if not options.discover_by_menu:
        return []
    labels = _nav_labels(page)
    if not labels:  # 导航还没挂出来 → 等一等再看（首批菜单要等接口）
        _wait_nav_ready(page, options)
        labels = _nav_labels(page)
    if not labels:
        return []
    start_url = _safe_url(page) or options.base_url
    start_route = _route_of(page) if _safe_url(page) else (urlparse(options.base_url).path or "/")
    probe = _MenuProbe(_Session(page, context), options, start_url, start_route, labels)
    found = _probe_menu_routes(probe)
    _return_to(page, start_url, options)  # 收尾回起点，供后续抓取落地页
    if found:
        result.notes.append(f"菜单点击发现路由 {len(found)} 条：{', '.join(found[:10])}")
    return found


# ============================================================================
# 元素抓取
# ============================================================================
_EXTRACT_JS_TEMPLATE = """
() => {
  const MAX = __MAX__;
  const seen = new Set();
  const isVisible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const s = window.getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
  };
  const cssPath = (el) => {
    const parts = [];
    let node = el;
    let depth = 0;
    while (node && node.nodeType === 1 && depth < 5) {
      if (node.id) { parts.unshift('#' + node.id); break; }
      let sel = node.tagName.toLowerCase();
      const cls = (node.getAttribute('class') || '').trim().split(/\\s+/).filter(Boolean).slice(0, 2);
      if (cls.length) sel += '.' + cls.join('.');
      const parent = node.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter((c) => c.tagName === node.tagName);
        if (same.length > 1) sel += ':nth-of-type(' + (same.indexOf(node) + 1) + ')';
      }
      parts.unshift(sel);
      node = node.parentElement;
      depth += 1;
    }
    return parts.join(' > ');
  };
  const textOf = (el) => String(
    el.innerText || el.value || el.getAttribute('aria-label')
    || el.getAttribute('placeholder') || el.getAttribute('title') || ''
  ).trim().replace(/\\s+/g, ' ').slice(0, 80);
  const out = [];
  const push = (el, kind) => {
    if (out.length >= MAX || seen.has(el)) return;
    seen.add(el);
    out.push({ selector: cssPath(el), kind: kind, text: textOf(el), visible: isVisible(el) });
  };
  document.querySelectorAll(__NAV__).forEach((el) => push(el, 'nav'));
  document.querySelectorAll(__BTN__).forEach((el) => push(el, 'button'));
  document.querySelectorAll(__FORM__).forEach((el) => {
    const tag = el.tagName.toLowerCase();
    push(el, el.getAttribute('contenteditable') === 'true' ? 'edit' : tag);
  });
  return out;
}
"""

_LINKS_JS_TEMPLATE = """
() => {
  const out = [];
  document.querySelectorAll('a[href]').forEach((a) => out.push(a.getAttribute('href')));
  ['data-href', 'data-url', 'data-path', 'data-route'].forEach((attr) => {
    document.querySelectorAll('[' + attr + ']').forEach((el) => out.push(el.getAttribute(attr)));
  });
  return out.filter((h) => !!h).slice(0, __MAX__);
}
"""


def _build_extract_js() -> str:
    """元素抓取脚本；选择器与上限取自本模块常量，避免两处漂移。"""
    return (
        _EXTRACT_JS_TEMPLATE.replace("__MAX__", str(MAX_ELEMENTS_PER_PAGE))
        .replace("__NAV__", json.dumps(_NAV_SELECTOR))
        .replace("__BTN__", json.dumps(_BUTTON_SELECTOR))
        .replace("__FORM__", json.dumps(_FORM_SELECTOR))
    )


def _build_links_js() -> str:
    """链接抓取脚本（含 data-* 路由提示：SPA 常无 `<a>`，靠 data 属性路由）。"""
    return _LINKS_JS_TEMPLATE.replace("__MAX__", str(MAX_HOME_LINKS))


def _crawl_links(page: Any) -> list[str]:
    """抓取当前页所有 `<a href>` 与 data-* 路由提示（供路由兜底）。"""
    try:
        links = page.evaluate(_build_links_js())
    except Exception:  # 链接爬取失败不影响主流程
        return []
    return [str(x) for x in links] if isinstance(links, list) else []


def _collect_page(
    page: Any,
    url: str,
    options: RuntimeUiOptions,
    sink: _ConsoleSink,
    mark: int,
) -> UiPage:
    """抓取单页：可达性、控制台错误、导航 / 表单 / 按钮元素。"""
    timeout_ms = _timeout_ms(options)
    path = urlparse(url).path or "/"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            # 只等「首屏差不多渲染完」；SPA 长轮询会让 networkidle 永不满足，
            # 照配置超时等会把十几个路由的遍历拖到数分钟。
            page.wait_for_load_state("networkidle", timeout=SETTLE_AFTER_GOTO_MS)
        except Exception:
            pass
    except Exception as exc:  # 单页失败只标记不可达，不中断遍历
        return UiPage(
            url=url,
            path=path,
            reachable=False,
            console_errors=[*sink.since(mark), f"[goto] {str(exc)[:200]}"],
        )

    try:
        title = str(page.title() or "")
    except Exception:  # 标题取值失败不影响元素抓取
        title = ""

    raw_elements: list[dict[str, Any]] = []
    try:
        got = page.evaluate(_build_extract_js())
        if isinstance(got, list):
            raw_elements = [x for x in got if isinstance(x, dict)]
    except Exception:  # 元素抓取失败仍保留该页（可达性已确立）
        raw_elements = []

    elements = [
        UiElement(
            selector=str(item.get("selector") or ""),
            kind=str(item.get("kind") or ""),
            text=str(item.get("text") or ""),
            visible=bool(item.get("visible")),
        )
        for item in raw_elements
        if item.get("selector")
    ]
    return UiPage(
        url=url,
        path=path,
        title=title,
        reachable=True,
        console_errors=sink.since(mark),
        elements=elements,
    )


def _absorb(result: RuntimeUiResult, ui_page: UiPage) -> None:
    """把单页结果并入总结果（按页聚合 + 展平元素/错误）。"""
    result.pages.append(ui_page)
    result.elements.extend(ui_page.elements)
    result.console_errors.extend(ui_page.console_errors)


def _sweep_pages(
    session: _Session,
    opts: RuntimeUiOptions,
    result: RuntimeUiResult,
    sink: _ConsoleSink,
    static_paths: list[str] | None,
) -> int:
    """抓取登录后落地页与各路由（含菜单点击发现），返回可达页数。"""
    page = session.page
    landing = _collect_page(page, _safe_url(page) or opts.base_url, opts, sink, len(sink.entries))
    _absorb(result, landing)
    menu_paths = _discover_menu_routes(page, session.context, opts, result)
    result.discovered_routes = list(menu_paths)
    routes = _resolve_routes(opts, static_paths, _crawl_links(page), menu_paths)
    for route in routes:
        if route == landing.path:
            continue
        mark = len(sink.entries)
        _absorb(result, _collect_page(page, urljoin(opts.base_url, route), opts, sink, mark))
    return sum(1 for p in result.pages if p.reachable)


# ============================================================================
# 产出：运行时发现 → 功能点（M3.4）
# ============================================================================
def _module_of_path(path: str) -> str:
    """由路径首段推导模块名（`/pc/tasks` → `pc`；根路径 → `root`）。"""
    segs = [s for s in (path or "").split("/") if s]
    return segs[0] if segs else "root"


def to_functional_points(result: RuntimeUiResult) -> list[FunctionalPoint]:
    """把运行时发现结果转成功能点（复用既有契约，**不新造字段**）。

    规则（见 `P3_UI生成_详细设计.md` §8.4）：
    - 每个**可达页面** → 1 条 `page` 功能点（`name` = 路径）；
    - 每个**含可见交互元素的可达页面** → 1 条 `component` 功能点（同一路径，`ftype` 不同）；
    - `file_path` = `runtime:<url>`（非真实文件路径，便于与静态来源区隔）；
    - `fp_id` = `fp_id_of(ftype, runtime:<url>, name)` → 同一环境重复跑编号稳定。

    只产出**可达**页面，不可达页（goto 失败）不产出功能点，避免生成必然失败的用例。
    """
    out: list[FunctionalPoint] = []
    seen: set[tuple[str, str]] = set()
    for page in result.reachable_pages():
        path = page.path or "/"
        module = _module_of_path(path)
        src = f"runtime:{page.url}"
        page_title = (page.title or "").strip()
        label = f"{page_title}｜{path}" if page_title else path
        candidates = [
            FunctionalPoint(
                fp_id=fp_id_of(FType.PAGE.value, src, path),
                ftype=FType.PAGE.value,
                file_path=src,
                name=path,
                title=f"页面 {label}",
                module=module,
                semantic=f"运行时发现页面 {path}（{page_title or '无标题'}）",
                description=page.url,
            )
        ]
        visible = [e for e in page.elements if e.visible]
        if visible:
            candidates.append(
                FunctionalPoint(
                    fp_id=fp_id_of(FType.COMPONENT.value, src, path),
                    ftype=FType.COMPONENT.value,
                    file_path=src,
                    name=path,
                    title=f"页面 {path}｜可交互元素（{len(visible)} 个）",
                    module=module,
                    semantic=f"运行时发现页面 {path} 含 {len(visible)} 个可见可交互元素",
                    description=page.url,
                )
            )
        for fp in candidates:
            key = (fp.ftype, fp.name)
            if key in seen:
                continue
            seen.add(key)
            out.append(fp)
    return out


# ============================================================================
# 主入口
# ============================================================================
def _launch_browser(playwright: Any, options: RuntimeUiOptions) -> Any:
    """启动浏览器：优先配置的 channel（可复用系统 Edge，免 150MB 内核下载）。"""
    kwargs: dict[str, Any] = {"headless": bool(options.headless)}
    if options.channel:
        kwargs["channel"] = options.channel
    try:
        return playwright.chromium.launch(**kwargs)
    except Exception as exc:  # 启动失败要带上环境信息提示用户
        hint = (
            "请先执行 `python -m playwright install chromium`，"
            "或在已装 Edge/Chrome 的机器上设 PLAYWRIGHT_CHANNEL=msedge"
        )
        channel = options.channel or "chromium"
        raise EngineError(f"浏览器启动失败（channel={channel}）：{exc}；{hint}") from exc


def _close_all(*resources: Any) -> None:
    """尽力关闭浏览器上下文（不留驻 cookie / storage）。"""
    for item in resources:
        if item is None:
            continue
        try:
            item.close()
        except Exception:  # 关闭失败不应覆盖主流程结论
            continue


def _record_summary(result: RuntimeUiResult, logged_in: bool, reachable: int) -> None:
    result.logged_in = logged_in
    result.notes.append(
        f"运行时发现完成：登录={'是' if logged_in else '否'}，"
        f"可达页面 {reachable}/{len(result.pages)}，元素 {len(result.elements)} 个，"
        f"菜单发现路由 {len(result.discovered_routes)} 条，"
        f"控制台错误 {len(result.console_errors)} 条"
    )
    log.info(
        "运行时 UI 发现完成",
        extra=log_extra(
            pages=len(result.pages),
            reachable=reachable,
            elements=len(result.elements),
            routes=len(result.discovered_routes),
            console_errors=len(result.console_errors),
            logged_in=logged_in,
        ),
    )


def discover_ui(
    options: RuntimeUiOptions | None = None,
    *,
    static_paths: list[str] | None = None,
) -> RuntimeUiResult:
    """打开被测环境，登录并遍历路由，抓取可交互元素与控制台错误。

    `static_paths` 为静态分析已提取的页面路径（路由优先级第 3 档）。
    """
    opts = options or RuntimeUiOptions()
    if opts.mode not in RUNTIME_UI_MODE_CHOICES:
        raise ValueError(f"未知的运行时 UI 发现模式：{opts.mode!r}，允许 {RUNTIME_UI_MODE_CHOICES}")
    if not opts.base_url:
        raise EngineError("运行时 UI 发现缺少被测地址（RUNTIME_BASE_URL）")
    if not _has_playwright():
        raise EngineError(_INSTALL_HINT)

    from playwright.sync_api import sync_playwright

    result = RuntimeUiResult(base_url=opts.base_url)
    sink = _ConsoleSink()
    browser = None
    context = None
    try:
        with sync_playwright() as pw:
            browser = _launch_browser(pw, opts)
            context = browser.new_context(ignore_https_errors=True)
            context.set_default_timeout(_timeout_ms(opts))
            _apply_token(context, opts, result)
            page = context.new_page()
            _attach_listeners(page, sink)
            session = _Session(page, context)
            logged_in = _login(page, opts, result)
            reachable = _sweep_pages(session, opts, result, sink, static_paths)
            if reachable == 0:
                raise EngineError(f"运行时 UI 发现失败：所有页面均不可达（{opts.base_url}）")
            _record_summary(result, logged_in, reachable)
    except EngineError:
        raise
    except Exception as exc:  # 浏览器驱动异常面很宽，统一转 EngineError
        raise EngineError(f"运行时 UI 发现失败：{exc}") from exc
    finally:
        _close_all(context, browser)
    return result
