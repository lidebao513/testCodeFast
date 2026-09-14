"""引擎 · 模块十（P3）：运行时浏览器 UI 发现。

设计定位：在「代码静态分析得到的 UI 功能点」之外，提供运行时验证通道——
用 Playwright 打开被测环境地址（用户提供 + 凭证经 .env 注入），真实渲染页面、
抓取可交互元素、记录控制台错误，反向补全 / 校验 UI 测试点。

依赖方向严格向下（只 import core），不感知 service / cli。
Playwright 采用**惰性导入**：未安装时不影响主链路（默认关闭），
由 `_has_playwright()` 探测，`discover_ui` 在缺失时给出可执行的安装指引。

凭证红线（见 `P3_UI生成_详细设计.md` §4.2）：
密码/令牌只从环境变量读取，**不进日志、不进产物、不进数据库**——本模块所有
日志调用点均不携带凭证字段，结果 note 也不回显密码。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from core.enums import RUNTIME_UI_MODE_CHOICES, RUNTIME_UI_PLAYWRIGHT
from core.errors import EngineError
from core.log import get_logger, log_extra


log = get_logger(__name__)


# ============================================================================
# 常量（选择器与上限集中于此，便于后续配置化）
# ============================================================================
# 导航类元素：登录后才可见的权限菜单是运行时发现相对静态分析的核心增量。
# 重要：SPA（React/Vue + antd 等）常**不用 `<a>`**——菜单是带类名的 div/li，
# 真实环境实测目标站整站 0 个 `<a>`，故这里同时覆盖「语义标签」与「常见菜单类名」。
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

# 单页元素上限（防爆：超长列表页可达数千个元素）
MAX_ELEMENTS_PER_PAGE = 200
# 首页链接爬取上限
MAX_HOME_LINKS = 300
# 单页控制台错误上限
MAX_CONSOLE_ERRORS_PER_PAGE = 20
# 控制台错误全站累积上限（防日志/结果爆炸）
MAX_CONSOLE_ERRORS_TOTAL = 500

# 登录选择器（按优先级排列；命中第一个即用）
_PASSWORD_SELECTORS = ("input[type=password]", 'input[name*="pass" i]')
_USER_SELECTORS = (
    "input[type=text]",
    "input[type=email]",
    'input[name*="user" i]',
    'input[name*="account" i]',
    'input[name*="mobile" i]',
    'input[name*="email" i]',
    "input:not([type])",
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
    # --- 本期新增（Additive）---
    channel: str = ""  # ""=自带 chromium；"msedge"/"chrome"=复用系统浏览器
    login_user: str = ""  # 表单登录账号
    login_password: str = ""  # 表单登录密码（不入库 / 不日志）
    login_url: str = ""  # 登录页地址；为空回退到 base_url
    routes: list[str] = field(default_factory=list)  # 显式路由清单（优先级最高）
    max_pages: int = 60  # 遍历页面上限（防爆）
    degraded: bool = False  # 是否降级为 requests 抓取（M3.5 落地，占位）


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


def _normalize_route(raw: str, base_url: str) -> str | None:
    """把一条候选路由规范化为同源路径；非同源 / 伪协议返回 None。"""
    item = (raw or "").strip()
    if not item or item.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None
    parts = urlparse(urljoin(base_url, item))
    if parts.scheme not in ("http", "https"):
        return None
    if _origin(base_url) and f"{parts.scheme}://{parts.netloc}" != _origin(base_url):
        return None  # 外链一律跳过
    path = parts.path or "/"
    return f"{path}?{parts.query}" if parts.query else path


def _resolve_routes(
    options: RuntimeUiOptions,
    static_paths: list[str] | None = None,
    discovered_links: list[str] | None = None,
) -> list[str]:
    """路由清单，按优先级合并去重后截断到上限。

    优先级：显式 routes > 静态 page 功能点路径 > 首页可点链接。
    """
    merged: list[str] = []
    seen: set[str] = set()
    limit = max(1, int(options.max_pages))
    for group in (options.routes, static_paths or [], discovered_links or []):
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


def _safe_url(page: Any) -> str:
    try:
        return str(page.url or "")
    except Exception:  # 页面已崩溃时取值失败属正常，不能因此中断发现
        return ""


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


def _login(page: Any, options: RuntimeUiOptions, result: RuntimeUiResult) -> bool:
    """检测登录表单并提交；无表单则视为已登录 / 匿名可访问。

    返回 True 表示执行了表单登录并成功；False 表示未执行登录（无凭证或无表单）。
    失败一律抛 `EngineError`（分类提示），**绝不回显密码**。
    """
    if not (options.login_user and options.login_password):
        result.notes.append("未提供账号密码：按匿名访问处理（仅公开页可见）")
        return False

    target = options.login_url or options.base_url
    timeout_ms = max(1, int(options.timeout)) * 1000
    try:
        page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as exc:  # 打开登录页失败即登录失败
        raise EngineError(f"登录失败：无法打开登录页 {target}（{exc}）") from exc

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
        submit.click()
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception as exc:  # 提交过程任何失败都归为登录失败
        raise EngineError(f"登录失败：提交登录表单出错（{exc}）") from exc

    if _first_match(page, _PASSWORD_SELECTORS) is not None:
        raise EngineError(
            "登录失败：提交后仍停留在登录页，请核对账号密码是否正确、"
            "或被测系统是否存在验证码 / 风控"
        )
    result.notes.append(
        f"表单登录成功（账号 {options.login_user}，密码不记录）；"
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
    """抓取当前页所有 `<a href>`（供路由兜底）。"""
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
    timeout_ms = max(1, int(options.timeout)) * 1000
    path = urlparse(url).path or "/"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:  # 长轮询页面永不 idle，超时后按当前 DOM 继续
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
    page: Any,
    opts: RuntimeUiOptions,
    result: RuntimeUiResult,
    sink: _ConsoleSink,
    static_paths: list[str] | None,
) -> int:
    """抓取登录后落地页与各路由，返回可达页数。"""
    landing = _collect_page(page, _safe_url(page) or opts.base_url, opts, sink, len(sink.entries))
    _absorb(result, landing)
    for route in _resolve_routes(opts, static_paths, _crawl_links(page)):
        if route == landing.path:
            continue
        mark = len(sink.entries)
        _absorb(result, _collect_page(page, urljoin(opts.base_url, route), opts, sink, mark))
    return sum(1 for p in result.pages if p.reachable)


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
        f"控制台错误 {len(result.console_errors)} 条"
    )
    log.info(
        "运行时 UI 发现完成",
        extra=log_extra(
            pages=len(result.pages),
            reachable=reachable,
            elements=len(result.elements),
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

    `static_paths` 为静态分析已提取的页面路径（路由优先级第 2 档）。
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
            context.set_default_timeout(max(1, int(opts.timeout)) * 1000)
            _apply_token(context, opts, result)
            page = context.new_page()
            _attach_listeners(page, sink)
            logged_in = _login(page, opts, result)
            reachable = _sweep_pages(page, opts, result, sink, static_paths)
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
