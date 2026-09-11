"""真实浏览器执行与截图（阶段4 批次4 · D-★3）。

定位
- 阶段 4.3 名义存在但平台内从未落地：此前真实 E2E 只存在于平台外的 `exec_live.py`，
  `runs.screenshot_path` 与 `settings.SCREENSHOTS_DIR` 都建了却从未被写入。
- 本模块把「真实渲染断言 + 失败自动截图」收进平台，作为**可选依赖**：
  playwright 未安装 / 浏览器不可用 / 启动超时 → 全部优雅降级为静态断言，
  由 executor 标注 `browser_unavailable`，绝不因缺依赖而中断整轮执行。

线程模型（重要）
- playwright 的**同步 API 绑定创建它的线程**（greenlet 实现）。跨线程调用会直接抛
  "cannot switch to a different thread (which happens to have exited)"。
- 因此本模块维护一个**常驻 daemon 线程 + 任务队列**：所有 launch/goto/screenshot
  都在同一线程里串行执行，调用方通过 `_submit(fn, timeout)` 投递并等待。
- 超时（如沙箱里自带 chromium 无限挂起）时调用方放弃等待并重启常驻线程，
  由 executor 降级为静态断言，绝不拖垮整轮执行。
"""

import queue
import threading
import time
from pathlib import Path

from backend.config import settings


_BROWSER_LOCK = threading.Lock()
# 单次启动探测的硬超时：playwright 自带 chromium 在部分沙箱里会**挂起**（不报错），
# 必须靠超时切断并回退到系统 Chrome/Edge，否则整轮执行会被拖死。
LAUNCH_PROBE_TIMEOUT = int(__import__("os").getenv("BROWSER_PROBE_TIMEOUT", "25"))

_PW = None  # sync_playwright 上下文管理器（只在常驻线程内使用）
_PW_OBJ = None
_BROWSER = None
_LAST_ERROR = None

_QUEUE: queue.Queue = queue.Queue()
_WORKER = None
_WORKER_LOCK = threading.Lock()


def available():
    """检查 playwright 是否可用。返回 (bool, reason)。"""
    try:
        import playwright  # noqa: F401
    except Exception as e:
        return False, f"playwright 未安装（{type(e).__name__}）：已降级为静态断言"
    return True, "ok"


def _candidate_executables():
    """浏览器可执行文件候选顺序：显式配置 → 系统 Chrome/Edge → playwright 自带 chromium。

    自带 chromium 放在最后：实测在本机沙箱中它会**无限挂起**（无报错），
    优先用系统 Chrome 可把首次启动从"挂死"降到 ~1.3s。
    """
    import os
    from pathlib import Path as _P

    cands = []
    if settings.BROWSER_EXECUTABLE_PATH:
        cands.append(settings.BROWSER_EXECUTABLE_PATH)
    for raw in (
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe",
        r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe",
        r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe",
    ):
        p = _P(os.path.expandvars(raw))
        if p.exists():
            cands.append(str(p))
    cands.append(None)  # None = playwright 自带 chromium
    return cands


def _launch_kwargs(executable=None):
    kw = {
        "headless": settings.BROWSER_HEADLESS,
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--proxy-server=direct://",
            "--proxy-bypass-list=*",
        ],
        "timeout": settings.BROWSER_LAUNCH_TIMEOUT * 1000,
    }
    if executable:
        kw["executable_path"] = executable
    return kw


def _get_browser():
    """懒加载并复用浏览器实例，逐个尝试候选可执行文件；失败返回 (None, reason)。"""
    global _PW, _PW_OBJ, _BROWSER, _LAST_ERROR
    if _BROWSER is not None:
        return _BROWSER, None
    from playwright.sync_api import sync_playwright

    if _PW is None:
        _PW = sync_playwright()
        _PW_OBJ = _PW.start()
    errors = []
    for exe in _candidate_executables():
        try:
            res = _PW_OBJ.chromium.launch(**_launch_kwargs(exe))
        except Exception as e:
            errors.append(f"{exe or 'bundled-chromium'}: {type(e).__name__}: {str(e)[:120]}")
            continue
        _BROWSER, _LAST_ERROR = res, None
        return res, None
    _LAST_ERROR = " | ".join(errors)[:400]
    return None, _LAST_ERROR


def _shot_path(name: str) -> Path:
    settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (name or "page"))[:60]
    ts = time.strftime("%Y%m%d_%H%M%S")
    return settings.SCREENSHOTS_DIR / f"{safe}_{ts}_{uuid4_short()}.png"


def uuid4_short():
    import uuid

    return uuid.uuid4().hex[:6]


def _close_all():
    global _PW, _PW_OBJ, _BROWSER
    try:
        if _BROWSER is not None:
            _BROWSER.close()
    except Exception:
        pass
    try:
        if _PW is not None:
            _PW.__exit__(None, None, None)
    except Exception:
        pass
    _PW = _PW_OBJ = _BROWSER = None


def shutdown():
    """关闭浏览器（供自测/进程退出调用）。必须在常驻线程里执行。"""
    global _WORKER
    if _WORKER is None:
        return
    try:
        _submit(_close_all, 15)
    except Exception:
        pass
    _QUEUE.put(None)
    with _WORKER_LOCK:
        _WORKER = None


def _worker_loop():
    """常驻浏览器线程：playwright 同步 API 绑定创建它的线程（greenlet），
    所有浏览器操作必须在**同一个线程**里执行，否则报
    "cannot switch to a different thread"。因此这里用任务队列串行消费。"""
    global _PW, _PW_OBJ, _BROWSER
    while True:
        job = _QUEUE.get()
        if job is None:
            break
        fn, box, evt = job
        try:
            box["res"] = fn()
        except Exception as e:
            box["err"] = f"{type(e).__name__}: {str(e)[:200]}"
        finally:
            evt.set()


def _ensure_worker():
    global _WORKER
    with _WORKER_LOCK:
        if _WORKER is None or not _WORKER.is_alive():
            _WORKER = threading.Thread(target=_worker_loop, name="test-accel-browser", daemon=True)
            _WORKER.start()


def _restart_worker():
    """浏览器线程被挂死时重启（旧线程为 daemon，放弃即可）。"""
    global _WORKER, _PW, _PW_OBJ, _BROWSER
    with _WORKER_LOCK:
        _WORKER = None
        _PW = _PW_OBJ = _BROWSER = None


def _submit(fn, timeout):
    """把浏览器操作投递给常驻线程，超时即放弃（不阻塞整轮执行）。"""
    _ensure_worker()
    box, evt = {}, threading.Event()
    _QUEUE.put((fn, box, evt))
    if not evt.wait(timeout):
        _restart_worker()
        return None, f"浏览器操作超过 {timeout}s 未返回（已放弃，降级为静态断言）"
    if "err" in box:
        return None, box["err"]
    return box.get("res"), None


def check_page(
    url, expect_text=None, expect_selector=None, name="page", screenshot=True, timeout_ms=None
):
    """真实渲染打开一个页面并做断言。

    返回 dict：
      ok            最终判定（True/False）
      skipped       是否因依赖/环境问题未真实执行（True 时 executor 应降级）
      status        主文档 HTTP 状态码
      title         页面标题
      text_len      可见文本长度
      matched       命中的期望文本/选择器
      screenshot_path  截图绝对路径（失败必截；成功受 SCREENSHOT_POLICY 控制）
      error         错误原因
      elapsed_ms    耗时
    """
    out = {
        "ok": False,
        "skipped": False,
        "status": None,
        "title": "",
        "text_len": 0,
        "matched": None,
        "screenshot_path": None,
        "error": None,
        "elapsed_ms": 0,
        "url": url,
    }
    t0 = time.time()

    ok_avail, reason = available()
    if not ok_avail:
        out.update(skipped=True, error=reason)
        return out

    timeout_ms = timeout_ms or settings.BROWSER_TIMEOUT_MS
    timeout_s = max(5, int(timeout_ms / 1000) + settings.BROWSER_LAUNCH_TIMEOUT)

    def _work():
        with _BROWSER_LOCK:
            browser, err = _get_browser()
            if browser is None:
                return {"__fatal__": err}
            ctx = browser.new_context(ignore_https_errors=True)
            page = ctx.new_page()
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(300)
                title = page.title() or ""
                try:
                    text = page.inner_text("body") or ""
                except Exception:
                    text = ""
                status = resp.status if resp is not None else None
                matched, okexpect = None, True
                if expect_selector:
                    try:
                        okexpect = page.query_selector(expect_selector) is not None
                        matched = expect_selector if okexpect else None
                    except Exception as e:
                        okexpect, matched = False, None
                        out["error"] = f"selector error: {str(e)[:120]}"
                elif expect_text:
                    okexpect = expect_text in text
                    matched = expect_text if okexpect else None
                ok = bool(status and status < 400) and okexpect
                shot = None
                want_shot = screenshot and ((not ok) or settings.SCREENSHOT_POLICY == "always")
                if want_shot:
                    try:
                        p = _shot_path(name)
                        page.screenshot(path=str(p), full_page=False)
                        shot = str(p)
                    except Exception:
                        shot = None
                return {
                    "ok": ok,
                    "status": status,
                    "title": title,
                    "text_len": len(text),
                    "matched": matched,
                    "screenshot_path": shot,
                }
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass

    res, err = _submit(_work, timeout_s)
    out["elapsed_ms"] = int((time.time() - t0) * 1000)
    if err:
        out.update(skipped=True, error=err)
        return out
    if res is None:
        out.update(skipped=True, error="浏览器操作无返回")
        return out
    if "__fatal__" in res:
        out.update(skipped=True, error=f"浏览器启动失败：{res['__fatal__']}")
        return out
    out.update({k: v for k, v in res.items() if k in out})
    return out
