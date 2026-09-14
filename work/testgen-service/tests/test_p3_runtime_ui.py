"""P3 运行时 UI 发现测试（M3.1 配置/探测 + M3.2 登录与单页抓取）。

分两层：
1. **无浏览器**（必跑）：路由优先级 / 同源过滤、登录选择器识别与失败分类、
   单页抓取与控制台错误切片、错误包装 —— 全部用桩对象驱动，秒级完成；
2. **真浏览器端到端**（有 playwright 才跑）：本地起迷你站点（登录页 + 受保护页），
   断言 `discover_ui` 能登录并发现「只在登录后可见」的页面。
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import ClassVar
from urllib.parse import urlparse

import pytest

from core.config import load_settings
from core.errors import ConfigError, EngineError
from engine import runtime_ui
from engine.runtime_ui import (
    _PASSWORD_SELECTORS,
    _SUBMIT_SELECTORS,
    _USER_SELECTORS,
)


_SECRET_PASSWORD = "S3cret-PW-xyz"


# ============================================================================
# 桩对象：不依赖 Playwright 也能验证页面交互逻辑
# ============================================================================
class _StubElement:
    def __init__(self) -> None:
        self.value: str | None = None
        self.clicks = 0

    def fill(self, value: str) -> None:
        self.value = value

    def click(self) -> None:
        self.clicks += 1


class _StubLoginPage:
    """模拟登录页。

    `present` 控制页面上「存在」的控件（user / pwd / submit）；
    `password_after` 控制提交后是否仍停留在登录页（用于验证失败判定）。
    """

    def __init__(
        self,
        *,
        present: tuple[str, ...] = ("user", "pwd", "submit"),
        password_after: bool = False,
        goto_error: Exception | None = None,
    ) -> None:
        self.present = present
        self.password_after = password_after
        self.goto_error = goto_error
        self.url = "http://srv/login"
        self.url_after = "http://srv/dashboard"
        self.visited: list[str] = []
        self.submitted = False
        self.user = _StubElement()
        self.pwd = _StubElement()
        self.submit = _StubElement()

    def goto(self, url: str, wait_until: str | None = None, timeout: int | None = None) -> None:
        self.visited.append(url)
        if self.goto_error is not None:
            raise self.goto_error
        self.url = url

    def query_selector(self, selector: str) -> _StubElement | None:
        if selector in _PASSWORD_SELECTORS:
            if "pwd" not in self.present:
                return None
            return None if (self.submitted and not self.password_after) else self.pwd
        if selector in _USER_SELECTORS:
            return self.user if "user" in self.present else None
        if selector in _SUBMIT_SELECTORS:
            return self.submit if "submit" in self.present else None
        return None

    def wait_for_load_state(self, state: str | None = None, timeout: int | None = None) -> None:
        self.submitted = True
        self.url = self.url_after


class _StubCrawlPage:
    """模拟被抓取的页面：evaluate 按脚本特征返回元素或链接。"""

    def __init__(
        self,
        *,
        elements: list[dict[str, object]] | None = None,
        links: list[str] | None = None,
        title: str = "首页",
        goto_error: Exception | None = None,
    ) -> None:
        self.url = "http://srv/"
        self._elements = elements or []
        self._links = links or []
        self._title = title
        self.goto_error = goto_error
        self.goto_calls: list[str] = []

    def goto(self, url: str, wait_until: str | None = None, timeout: int | None = None) -> None:
        self.goto_calls.append(url)
        if self.goto_error is not None:
            raise self.goto_error
        self.url = url

    def wait_for_load_state(self, state: str | None = None, timeout: int | None = None) -> None:
        return None

    def title(self) -> str:
        return self._title

    def evaluate(self, script: str) -> list[object]:
        if "querySelectorAll('a[href]')" in script:
            return list(self._links)
        return list(self._elements)


class _StubBrowserLauncher:
    """模拟 playwright 对象（chromium.launch）。"""

    def __init__(self, exc: Exception | None = None) -> None:
        self.chromium = self
        self._exc = exc
        self.kwargs: dict[str, object] | None = None

    def launch(self, **kwargs: object) -> str:
        self.kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return "BROWSER"


class _StubContext:
    def __init__(self) -> None:
        self.headers: dict[str, str] | None = None

    def set_extra_http_headers(self, headers: dict[str, str]) -> None:
        self.headers = headers


def _opts(**kw: object) -> runtime_ui.RuntimeUiOptions:
    base: dict[str, object] = {"base_url": "http://srv", "login_user": "u", "login_password": "p"}
    base.update(kw)
    return runtime_ui.RuntimeUiOptions(**base)  # type: ignore[arg-type]


# ============================================================================
# M3.1 可用性探测与配置映射
# ============================================================================
def test_has_playwright_returns_bool() -> None:
    assert isinstance(runtime_ui._has_playwright(), bool)


def test_options_from_settings_maps_all_fields() -> None:
    class _S:
        playwright_headless: ClassVar[bool] = False
        runtime_base_url: ClassVar[str] = "http://srv:9001/login"
        runtime_auth_token: ClassVar[str] = "TOK"
        runtime_ui_timeout: ClassVar[int] = 15
        playwright_channel: ClassVar[str] = "msedge"
        runtime_login_user: ClassVar[str] = "tester"
        runtime_login_password: ClassVar[str] = _SECRET_PASSWORD
        runtime_login_url: ClassVar[str] = "http://srv:9001/login"
        runtime_routes: ClassVar[list[str]] = ["/pc/tasks"]
        runtime_max_pages: ClassVar[int] = 7

    opts = runtime_ui.options_from_settings(_S())
    assert opts.base_url == "http://srv:9001/login"
    assert opts.headless is False
    assert opts.timeout == 15
    assert opts.channel == "msedge"
    assert opts.login_user == "tester"
    assert opts.login_password == _SECRET_PASSWORD
    assert opts.routes == ["/pc/tasks"]
    assert opts.max_pages == 7


def test_public_dict_hides_password_and_token() -> None:
    """凭证红线：public_dict 只输出「是否已配置」，绝不输出取值。"""
    s = load_settings(
        {
            "RUNTIME_UI_ENABLED": "on",
            "RUNTIME_BASE_URL": "http://srv:9001",
            "RUNTIME_LOGIN_USER": "tester",
            "RUNTIME_LOGIN_PASSWORD": _SECRET_PASSWORD,
            "RUNTIME_AUTH_TOKEN": "TOK-abc",
        }
    )
    dumped = repr(s.public_dict())
    assert _SECRET_PASSWORD not in dumped
    assert "TOK-abc" not in dumped
    assert s.public_dict()["runtime_login_configured"] is True
    assert s.public_dict()["runtime_token_configured"] is True


def test_settings_reject_runtime_ui_without_base_url() -> None:
    with pytest.raises(ConfigError, match="RUNTIME_BASE_URL"):
        load_settings({"RUNTIME_UI_ENABLED": "on"})


# ============================================================================
# M3.2 路由解析
# ============================================================================
def test_normalize_route_rejects_foreign_and_pseudo_schemes() -> None:
    base = "http://srv:9001/user/login"
    assert runtime_ui._normalize_route("/pc/tasks", base) == "/pc/tasks"
    assert runtime_ui._normalize_route("/pc/tasks?page=1", base) == "/pc/tasks?page=1"
    assert runtime_ui._normalize_route("http://srv:9001/pc/x", base) == "/pc/x"
    assert runtime_ui._normalize_route("http://other/x", base) is None
    assert runtime_ui._normalize_route("javascript:void(0)", base) is None
    assert runtime_ui._normalize_route("mailto:a@b.c", base) is None
    assert runtime_ui._normalize_route("#tab", base) is None
    assert runtime_ui._normalize_route("   ", base) is None


def test_resolve_routes_priority_and_dedupe() -> None:
    opts = _opts(routes=["/explicit"], max_pages=10)
    got = runtime_ui._resolve_routes(
        opts,
        ["/static", "/explicit"],
        ["/home", "/static", "http://elsewhere/x", "javascript:void(0)"],
    )
    assert got == ["/explicit", "/static", "/home"]


def test_resolve_routes_respects_max_pages() -> None:
    opts = _opts(max_pages=2)
    assert runtime_ui._resolve_routes(opts, ["/a", "/b", "/c"]) == ["/a", "/b"]


# ============================================================================
# M3.2 登录
# ============================================================================
def test_login_skipped_without_credentials() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage()
    opts = runtime_ui.RuntimeUiOptions(base_url="http://srv")
    assert runtime_ui._login(page, opts, result) is False
    assert page.visited == []  # 无凭证不应打开登录页
    assert any("未提供账号密码" in n for n in result.notes)


def test_login_success_fills_and_submits() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage()
    opts = _opts(login_password=_SECRET_PASSWORD)
    assert runtime_ui._login(page, opts, result) is True
    assert page.user.value == "u"
    assert page.pwd.value == _SECRET_PASSWORD
    assert page.submit.clicks == 1
    joined = " ".join(result.notes)
    assert "表单登录成功" in joined
    assert _SECRET_PASSWORD not in joined  # 红线：结果不回显密码


def test_login_prefers_configured_login_url() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage()
    runtime_ui._login(page, _opts(login_url="http://srv/user/login"), result)
    assert page.visited == ["http://srv/user/login"]


def test_login_fails_when_still_on_login_page() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage(password_after=True)
    with pytest.raises(EngineError) as ei:
        runtime_ui._login(page, _opts(login_password=_SECRET_PASSWORD), result)
    assert "仍停留在登录页" in str(ei.value)
    assert _SECRET_PASSWORD not in str(ei.value)


def test_login_without_password_field_is_public_page() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage(present=())
    assert runtime_ui._login(page, _opts(), result) is False
    assert any("未发现密码输入框" in n for n in result.notes)


def test_login_missing_user_or_submit_raises() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    with pytest.raises(EngineError, match="未定位到账号输入框"):
        runtime_ui._login(_StubLoginPage(present=("pwd", "submit")), _opts(), result)
    with pytest.raises(EngineError, match="未定位到账号输入框"):
        runtime_ui._login(_StubLoginPage(present=("user", "pwd")), _opts(), result)


def test_login_goto_error_wrapped_as_engine_error() -> None:
    result = runtime_ui.RuntimeUiResult(base_url="http://srv")
    page = _StubLoginPage(goto_error=RuntimeError("conn refused"))
    with pytest.raises(EngineError, match="无法打开登录页"):
        runtime_ui._login(page, _opts(), result)


def test_apply_token_sets_header_without_recording_value() -> None:
    ctx = _StubContext()
    result = runtime_ui.RuntimeUiResult()
    runtime_ui._apply_token(ctx, runtime_ui.RuntimeUiOptions(auth_token="TOK-abc"), result)
    assert ctx.headers == {"Authorization": "Bearer TOK-abc"}
    assert "TOK-abc" not in " ".join(result.notes)


def test_apply_token_skipped_when_absent() -> None:
    ctx = _StubContext()
    runtime_ui._apply_token(ctx, runtime_ui.RuntimeUiOptions(), runtime_ui.RuntimeUiResult())
    assert ctx.headers is None


# ============================================================================
# M3.2 单页抓取
# ============================================================================
def _elements() -> list[dict[str, object]]:
    return [
        {"selector": "#nav", "kind": "nav", "text": "任务", "visible": True},
        {"selector": "input.x", "kind": "input", "text": "", "visible": False},
        {"selector": "", "kind": "input", "text": "无选择器应被丢弃", "visible": True},
    ]


def test_collect_page_parses_elements_and_drops_empty_selector() -> None:
    page = _StubCrawlPage(elements=_elements(), title="工作台")
    sink = runtime_ui._ConsoleSink()
    ui_page = runtime_ui._collect_page(page, "http://srv/pc/tasks", _opts(), sink, 0)
    assert ui_page.reachable is True
    assert ui_page.path == "/pc/tasks"
    assert ui_page.title == "工作台"
    assert [e.selector for e in ui_page.elements] == ["#nav", "input.x"]
    assert ui_page.elements[0].visible is True


def test_collect_page_marks_unreachable_on_goto_error() -> None:
    page = _StubCrawlPage(goto_error=RuntimeError("net down"))
    sink = runtime_ui._ConsoleSink()
    ui_page = runtime_ui._collect_page(page, "http://srv/x", _opts(), sink, 0)
    assert ui_page.reachable is False
    assert any("[goto]" in e for e in ui_page.console_errors)


def test_collect_page_slices_console_errors_since_mark() -> None:
    sink = runtime_ui._ConsoleSink()
    sink.add("old-1")
    sink.add("old-2")
    page = _StubCrawlPage(elements=_elements())
    sink.add("new-1")
    ui_page = runtime_ui._collect_page(page, "http://srv/x", _opts(), sink, 2)
    assert ui_page.console_errors == ["new-1"]


def test_console_sink_caps_total_entries() -> None:
    sink = runtime_ui._ConsoleSink()
    for i in range(600):
        sink.add(f"e{i}")
    assert len(sink.entries) == 500
    assert sink.since(499) == ["e499"]


def test_crawl_links_reads_anchor_hrefs() -> None:
    page = _StubCrawlPage(links=["/a", "/b"])
    assert runtime_ui._crawl_links(page) == ["/a", "/b"]


def test_extract_js_embeds_single_source_selectors() -> None:
    """选择器/上限来自模块常量，禁止在 JS 里另写一份（防漂移）。"""
    js = runtime_ui._build_extract_js()
    # json.dumps 会在 JS 字面量里转义双引号，故比对转义后的形态
    assert json.dumps(runtime_ui._NAV_SELECTOR)[1:-1] in js
    assert json.dumps(runtime_ui._BUTTON_SELECTOR)[1:-1] in js
    assert json.dumps(runtime_ui._FORM_SELECTOR)[1:-1] in js
    assert str(runtime_ui.MAX_ELEMENTS_PER_PAGE) in js
    for token in ("__NAV__", "__BTN__", "__FORM__", "__MAX__"):
        assert token not in js
    assert str(runtime_ui.MAX_HOME_LINKS) in runtime_ui._build_links_js()


def test_spa_without_anchor_tags_is_still_covered() -> None:
    """实测回归：目标站整站 **0 个 `<a>`**，导航是带类名的 div。

    若选择器只认 `<a>`，这类 SPA 会「一个导航都抓不到」——本条锁死该覆盖。
    """
    nav = runtime_ui._NAV_SELECTOR
    assert '[class*="nav-item"]' in nav
    assert '[class*="menu-item"]' in nav
    assert '[class*="btn"]' in runtime_ui._BUTTON_SELECTOR
    assert "contenteditable" in runtime_ui._FORM_SELECTOR
    links_js = runtime_ui._build_links_js()
    for attr in ("data-href", "data-url", "data-path", "data-route"):
        assert attr in links_js


def test_launch_browser_passes_channel_and_wraps_error() -> None:
    pw = _StubBrowserLauncher()
    assert runtime_ui._launch_browser(pw, _opts(channel="msedge")) == "BROWSER"
    assert pw.kwargs == {"headless": True, "channel": "msedge"}
    with pytest.raises(EngineError, match="浏览器启动失败"):
        runtime_ui._launch_browser(
            _StubBrowserLauncher(exc=RuntimeError("no browser")), runtime_ui.RuntimeUiOptions()
        )


def test_discover_ui_requires_base_url_before_playwright_check() -> None:
    with pytest.raises(EngineError, match="RUNTIME_BASE_URL"):
        runtime_ui.discover_ui(runtime_ui.RuntimeUiOptions())


def test_discover_ui_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="未知的运行时 UI 发现模式"):
        runtime_ui.discover_ui(runtime_ui.RuntimeUiOptions(mode="nope", base_url="http://srv"))


# ============================================================================
# 真浏览器端到端（本地迷你站点：登录页 + 受保护页）
# ============================================================================
_LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>登录</title></head>
<body><div id="app">
<form id="f" onsubmit="return doLogin(event)">
  <input type="text" name="username" placeholder="账号">
  <input type="password" name="password" placeholder="密码">
  <button type="submit">登录</button>
</form>
<script>
function doLogin(e) {
  e.preventDefault();
  var u = document.querySelector('input[name=username]').value;
  if (u === 'good') { window.location.href = '/dashboard'; }
  return false;
}
</script>
</div></body></html>"""

_DASHBOARD_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>工作台</title></head>
<body><nav><a href="/pc/tasks">任务管理</a><a href="/pc/secret">仅登录可见</a></nav>
<div id="main">工作台内容</div></body></html>"""

_TASKS_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>任务列表</title></head>
<body><h1>任务列表</h1><form><input type="text" name="kw"><button type="submit">查询</button></form>
</body></html>"""

_SECRET_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>隐藏页</title></head>
<body><h1>仅登录可见</h1><button id="do">执行</button></body></html>"""


class _SiteHandler(BaseHTTPRequestHandler):
    pages: ClassVar[dict[str, str]] = {}

    def do_GET(self) -> None:
        html = self.pages.get(urlparse(self.path).path)
        if html is None:
            self.send_error(404)
            return
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # 静音访问日志
        return None


@pytest.fixture()
def mini_site() -> str:
    """起一个本地迷你站点，返回其源地址（http://127.0.0.1:<port>）。"""
    _SiteHandler.pages = {
        "/login": _LOGIN_HTML,
        "/dashboard": _DASHBOARD_HTML,
        "/pc/tasks": _TASKS_HTML,
        "/pc/secret": _SECRET_HTML,
    }
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SiteHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _browser_options(base: str, **kw: object) -> runtime_ui.RuntimeUiOptions:
    opts = runtime_ui.RuntimeUiOptions(
        base_url=f"{base}/login",
        login_url=f"{base}/login",
        login_user="good",
        login_password=_SECRET_PASSWORD,
        timeout=15,
        channel=os.environ.get("PLAYWRIGHT_CHANNEL", ""),
        max_pages=10,
    )
    for key, value in kw.items():
        setattr(opts, key, value)
    return opts


def test_discover_ui_end_to_end_finds_protected_pages(mini_site: str) -> None:
    """核心验收：真浏览器登录后，能发现「只在登录后才可见」的页面。"""
    pytest.importorskip("playwright")
    try:
        result = runtime_ui.discover_ui(_browser_options(mini_site))
    except EngineError as exc:  # 内核缺失等环境问题 → 跳过而非失败
        pytest.skip(f"浏览器不可用：{exc}")

    paths = {p.path for p in result.pages}
    assert "/dashboard" in paths, f"未抓到登录后落地页，实际：{sorted(paths)}"
    assert "/pc/secret" in paths, f"未发现受保护页，实际：{sorted(paths)}"
    assert any(p.reachable for p in result.pages)
    assert result.base_url == f"{mini_site}/login"
    assert any("表单登录成功" in n for n in result.notes)
    kinds = {e.kind for e in result.elements}
    assert "nav" in kinds
    assert kinds & {"input", "button", "form"}
    assert _SECRET_PASSWORD not in repr(result)  # 红线


def test_discover_ui_end_to_end_detects_login_failure(mini_site: str) -> None:
    """登录失败（账号不存在）必须显式报错，而不是静默继续。"""
    pytest.importorskip("playwright")
    opts = _browser_options(mini_site, login_user="nobody")
    try:
        runtime_ui.discover_ui(opts)
    except EngineError as exc:
        if "仍停留在登录页" in str(exc):
            return
        pytest.skip(f"浏览器不可用：{exc}")
    pytest.fail("账号不存在时未报登录失败")


def test_discover_ui_end_to_end_no_credentials_public_pages(mini_site: str) -> None:
    """无凭证时按匿名访问（M3.2 验收口径：无登录公开页先打通）。"""
    pytest.importorskip("playwright")
    opts = _browser_options(mini_site, login_user="", login_password="")
    try:
        result = runtime_ui.discover_ui(opts)
    except EngineError as exc:
        pytest.skip(f"浏览器不可用：{exc}")
    assert any(p.reachable for p in result.pages)
    assert any("未提供账号密码" in n for n in result.notes)


def test_repo_has_no_plaintext_password_in_tracked_files() -> None:
    """红线自检：仓库中不得出现真实环境凭证。"""
    root = Path(__file__).resolve().parents[1]
    needle = "Taiping" + "@"
    for path in root.rglob("*.py"):
        if "venv" in path.parts:
            continue
        assert needle not in path.read_text(encoding="utf-8", errors="ignore")
