"""阶段4 批次4 自测：D-★3（真实浏览器 + 截图）/ D-②8（凭据外置）。

验证项
 B4-4-1  浏览器可用且能自动发现可执行文件（自带 chromium 在沙箱会挂起，需回退系统 Chrome）
 B4-4-2  真实渲染断言：200 页面 → ok，标题/可见文本被真实读取
 B4-4-3  失败自动截图：非 2xx 页面 → ok=False 且生成截图文件
 B4-4-4  截图落在 settings.SCREENSHOTS_DIR（此前该目录从未被写入）
 B4-4-5  expect_text 断言：命中即过、未命中即失败
 B4-4-6  执行器集成：page 类用例走真实浏览器 → pass / fail
 B4-4-7  runs.screenshot_path 被真实写入 DB（此前该字段从未使用）
 B4-4-8  优雅降级：浏览器不可用时回落静态断言且不抛异常
 B4-4-9  目标不可达时不挂死：超时后降级（沙箱 chromium 挂起场景）
 B4-4-10 D-②8 exec_live.py 已无明文凭据，改由环境变量注入
 B4-4-11 D-②8 产物目录与结果文件已脱敏，且提供 .env.example
"""

import json
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import backend.db as db
from backend.config import PROJECT_ROOT, settings
from backend.modules import browser
from backend.modules.executor import executor
from backend.modules.project_manager import pm


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"
ART = PROJECT_ROOT.parent / "research-agent-test"

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


PAGE_OK = (
    "<!doctype html><html><head><title>首页</title></head>"
    "<body><h1>欢迎使用福享 Agent</h1>"
    "<p>这是一个用于真实渲染断言的页面。</p></body></html>"
).encode()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=b""):
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/ok":
            return self._send(200, PAGE_OK)
        if self.path == "/boom":
            return self._send(
                500,
                "<html><head><title>出错</title></head><body>Internal Server Error</body></html>",
            )
        return self._send(404, "<html><head><title>404</title></head><body>not found</body></html>")


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
MOCK = f"http://127.0.0.1:{port}"


def _case(pid, title, path, kind="page"):
    steps = json.dumps(
        [
            {
                "action": "ui_probe",
                "kind": kind,
                "path": path,
                "file": "frontend/app/src/App.tsx",
                "expect": "页面可正常打开",
            }
        ],
        ensure_ascii=False,
    )
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cases (project_id, title, steps, ctype, status, review_status,
                              priority, module, case_type, test_type, tc_no)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, title, steps, "e2e", "generated", "approved", "P1", "前端", "正常", "全量", title),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def main():
    t0 = time.time()
    db.init_db()

    # ---------- B4-4-1 浏览器可用性与可执行文件发现 ----------
    ok_avail, reason = browser.available()
    cands = browser._candidate_executables()
    has_real = any(c and Path(c).exists() for c in cands)
    check(
        "B4-4-1 playwright 可用且能自动发现系统浏览器可执行文件",
        ok_avail and has_real,
        f"available={ok_avail}({reason}), 首个候选={cands[0]}",
    )

    # ---------- B4-4-2 真实渲染断言 ----------
    rep = browser.check_page(MOCK + "/ok", name="b44_ok")
    check(
        "B4-4-2 真实渲染断言：200 页面 → ok=True，标题被真实读取",
        rep.get("ok") is True and rep.get("status") == 200 and "首页" in (rep.get("title") or ""),
        f"ok={rep.get('ok')}, status={rep.get('status')}, title={rep.get('title')!r}, "
        f"text_len={rep.get('text_len')}, {rep.get('elapsed_ms')}ms",
    )
    check(
        "B4-4-2b 可见文本被真实读取（非空）",
        (rep.get("text_len") or 0) > 0,
        f"text_len={rep.get('text_len')}",
    )

    # ---------- B4-4-3 / 4-4-4 失败自动截图 ----------
    rep500 = browser.check_page(MOCK + "/boom", name="b44_boom")
    shot = rep500.get("screenshot_path")
    check(
        "B4-4-3 非 2xx 页面 → ok=False 且自动截图",
        rep500.get("ok") is False and rep500.get("status") == 500 and bool(shot),
        f"ok={rep500.get('ok')}, status={rep500.get('status')}, shot={shot}",
    )
    check(
        "B4-4-4 截图文件真实生成于 settings.SCREENSHOTS_DIR",
        bool(shot) and Path(shot).exists() and Path(shot).parent == Path(settings.SCREENSHOTS_DIR),
        f"path={shot}, exists={bool(shot) and Path(shot).exists()}",
    )

    # ---------- B4-4-5 expect_text 断言 ----------
    r_hit = browser.check_page(MOCK + "/ok", expect_text="欢迎使用", name="b44_hit")
    r_miss = browser.check_page(MOCK + "/ok", expect_text="绝不会出现的文案", name="b44_miss")
    check(
        "B4-4-5 expect_text 断言：命中即过、未命中即失败",
        r_hit.get("ok") is True and r_miss.get("ok") is False,
        f"hit={r_hit.get('ok')}, miss={r_miss.get('ok')}",
    )

    # ---------- B4-4-6 / 4-4-7 执行器集成 ----------
    name = "b44-browser"
    p = pm.find_by_name(name)
    pid = p["id"] if p else pm.add(name=name, local_path=str(TARGET), ptype="pc", base_url=MOCK)
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cases WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM runs WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()
    c_ok = _case(pid, "B44-OK", "/ok")
    c_ng = _case(pid, "B44-NG", "/boom")

    settings.RA_FRONTEND_URL = MOCK
    res = executor.run_project(pid, max_workers=1, use_browser=True)
    m = {r["case_id"]: r for r in res}
    check(
        "B4-4-6 执行器集成：page 类用例走真实浏览器 → 200 通过 / 500 失败",
        m[c_ok]["status"] == "pass" and m[c_ng]["status"] == "fail",
        f"ok={m[c_ok]['status']}, ng={m[c_ng]['status']}, reason={m[c_ng].get('reason')}",
    )

    bid = executor.last_batch_id
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT case_id, screenshot_path FROM runs WHERE batch_id=?", (bid,))
    rows = {r["case_id"]: r["screenshot_path"] for r in cur.fetchall()}
    conn.close()
    check(
        "B4-4-7 runs.screenshot_path 被真实写入 DB（此前从未使用）",
        bool(rows.get(c_ng)) and Path(rows[c_ng]).exists() and not rows.get(c_ok),
        f"失败用例截图={rows.get(c_ng)}, 通过用例截图={rows.get(c_ok)}（on_fail 策略下应为空）",
    )

    # ---------- B4-4-8 优雅降级 ----------
    orig_check = browser.check_page
    browser.check_page = lambda *a, **k: {"ok": False, "skipped": True, "error": "模拟浏览器不可用"}
    try:
        res2 = executor.run_project(pid, max_workers=1, use_browser=True)
    finally:
        browser.check_page = orig_check
    m2 = {r["case_id"]: r for r in res2}
    check(
        "B4-4-8 浏览器不可用时优雅降级为静态断言且不抛异常",
        m2[c_ok]["status"] in ("structural_only", "fail")
        and m2[c_ok].get("browser_unavailable") is True
        and "降级" in (m2[c_ok].get("reason") or ""),
        f"status={m2[c_ok]['status']}, 降级原因={str(m2[c_ok].get('browser_error'))[:60]}",
    )

    # ---------- B4-4-9 目标不可达不挂死 ----------
    dead = MOCK.rsplit(":", 1)[0] + ":9"  # 无人监听的端口
    t1 = time.time()
    rep_dead = browser.check_page(dead + "/x", name="b44_dead")
    dt = time.time() - t1
    check(
        "B4-4-9 目标不可达：超时后降级返回，不挂死整轮执行",
        rep_dead.get("skipped") is True and dt < 120,
        f"skipped={rep_dead.get('skipped')}, 耗时={dt:.1f}s, err={str(rep_dead.get('error'))[:60]}",
    )

    # 挂死场景：模拟浏览器操作永不返回 → 硬超时放弃 + 重启常驻线程
    t2 = time.time()
    res_hang, err_hang = browser._submit(lambda: time.sleep(120), 3)
    dt_hang = time.time() - t2
    check(
        "B4-4-9b 浏览器操作挂死：3s 硬超时后放弃并重启线程（不拖垮整轮）",
        res_hang is None and "超过 3s" in (err_hang or "") and dt_hang < 8,
        f"耗时={dt_hang:.1f}s, err={err_hang}",
    )
    rep_after = browser.check_page(MOCK + "/ok", name="b44_after_restart")
    check(
        "B4-4-9c 线程重启后浏览器能力自动恢复",
        rep_after.get("ok") is True,
        f"ok={rep_after.get('ok')}",
    )

    # ---------- B4-4-10 / 4-4-11 凭据外置 ----------
    live = ART / "exec_live.py"
    txt = live.read_text(encoding="utf-8") if live.exists() else ""
    leak = re.search(r"(Tp0326@test|test_ft001@ft\.cntaiping\.com|260326)", txt)
    check(
        "B4-4-10 D-②8 exec_live.py 已无明文账号/密码/口令",
        bool(txt)
        and leak is None
        and 'os.getenv("RA_WEB_ACCOUNT"' in txt
        and 'os.getenv("RA_TARGET_BASE"' in txt,
        f"命中明文={leak.group(0) if leak else '无'}，已改用环境变量读取",
    )

    ex_env = ART / ".env.example"
    keys_ok = False
    if ex_env.exists():
        c = ex_env.read_text(encoding="utf-8")
        keys_ok = all(
            k in c for k in ("RA_TARGET_BASE", "RA_WEB_ACCOUNT", "RA_WEB_PASSWORD", "RA_WEB_OTP")
        )
    res_json = ART / "live_test_results.json"
    masked = True
    if res_json.exists():
        j = json.loads(res_json.read_text(encoding="utf-8"))
        masked = "***" in (j.get("account") or "")
    check(
        "B4-4-11 D-②8 提供 .env.example 且历史结果文件账号已脱敏",
        keys_ok and masked,
        f".env.example 关键键齐全={keys_ok}, 结果脱敏={masked}",
    )

    browser.shutdown()
    srv.shutdown()

    passed = sum(1 for _, ok, _ in _results if ok)
    print("\n" + "=" * 60)
    print(f"==== 批次4 自测汇总：{passed}/{len(_results)} 通过，耗时 {time.time() - t0:.1f}s ====")
    for name_, ok, detail in _results:
        if not ok:
            print(f"  [FAILED] {name_} — {detail}")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
