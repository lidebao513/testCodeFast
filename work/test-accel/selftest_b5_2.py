"""阶段5 批次1 自测：P5-★4（异步任务化 + webhook 回调）+ P5-②1（cases.status 语义清理）。

验证项
 B5-2-1  async + webhook_url：后台执行结束后回调 webhook，payload 含 batch_id/state=done/summary
 B5-2-2  webhook state=cancelled：执行中途取消后，回调 state=cancelled（不丢已执行部分）
 B5-2-3  webhook 缺省不崩：无 webhook_url 时 async 仍能 done
 B5-2-4  P5-②1：执行后 cases.status 仍为生命周期值（generated），执行结论只落 runs.status + cases.last_result
 B5-2-5  /execute/tasks 列出任务（含刚结束的 batch）
"""

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import backend.db as db
from backend.config import settings
from backend.main import app
from backend.modules.executor import executor
from backend.modules.project_manager import pm


_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


class _HookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(n) if n else b""
        self.server.received.append(json.loads(body.decode("utf-8")))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')
        sys.stdout.write(f"[webhook] 收到回调: {body[:160].decode('utf-8', 'ignore')}\n")

    def log_message(self, *a):
        pass


def webhook_server():
    srv = HTTPServer(("127.0.0.1", 0), _HookHandler)
    srv.received = []
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/hook"


def make_project(name, n_cases):
    p = pm.find_by_name(name)
    pid = (
        p["id"]
        if p
        else pm.add(name=name, local_path=str(ROOT), ptype="pc", base_url="http://localhost:9")
    )
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cases WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM runs WHERE project_id=?", (pid,))
    for i in range(n_cases):
        cur.execute(
            """INSERT INTO cases (project_id, title, steps, ctype, status,
                                  review_status, priority, module, case_type, test_type)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (pid, f"case-{i}", "[]", "api", "generated", "approved", "P1", "模块X", "正常", "全量"),
        )
    conn.commit()
    conn.close()
    return pid


def make_slow(status="pass", delay=0.03):
    def _slow(c, proj, ctx, service_up):
        time.sleep(delay)
        return {"status": status, "reason": "patched", "log": ""}

    return _slow


def wait_state(client, pid, bid, want, timeout=15):
    deadline = time.time() + timeout
    final = None
    while time.time() < deadline:
        s = client.get(f"/api/projects/{pid}/execute/status", params={"batch_id": bid}).json()
        final = s.get("status")
        if final and final["state"] in want:
            return final
        time.sleep(0.1)
    return final


def main():
    t0 = time.time()
    settings.REVIEW_GATE = False
    settings.ENABLE_DYNAMIC_PROBE = False
    db.init_db()

    pid = make_project("b5-webhook", 60)
    print(f"[setup] 项目 {pid}：60 条空步骤用例")

    # ---------- B5-2-1 async + webhook：结束回调 state=done ----------
    srv, url = webhook_server()
    orig = executor._safe_run
    executor._safe_run = make_slow("pass", 0.02)
    try:
        client = TestClient(app)
        r = client.post(
            f"/api/projects/{pid}/execute",
            json={"max_workers": 1, "with_report": False, "async_mode": True, "webhook_url": url},
        )
        body = r.json()
        bid = body["batch_id"]
        check(
            "B5-2-1 async_mode 返回 batch_id 且 webhook 标记开启",
            r.status_code == 200 and body.get("async") and bid and body.get("webhook"),
            f"http={r.status_code}, webhook={body.get('webhook')}",
        )
        final = wait_state(client, pid, bid, ("done",))
        check(
            "B5-2-1b 执行到 done",
            final and final["state"] == "done" and final["done"] == 60,
            f"state={final['state'] if final else None}, done={final['done'] if final else None}",
        )
        # 等待 webhook 异步发出
        for _ in range(50):
            if srv.received:
                break
            time.sleep(0.1)
        check(
            "B5-2-1c webhook 被回调且 payload 含 batch_id/state=done/summary.total",
            len(srv.received) == 1
            and srv.received[0]["batch_id"] == bid
            and srv.received[0]["state"] == "done"
            and srv.received[0]["summary"]["total"] == 60,
            f"received={srv.received}",
        )
    finally:
        executor._safe_run = orig
        srv.shutdown()

    # ---------- B5-2-2 中途取消 → webhook state=cancelled ----------
    srv2, url2 = webhook_server()
    executor._safe_run = make_slow("pass", 0.03)
    try:
        client = TestClient(app)
        r = client.post(
            f"/api/projects/{pid}/execute",
            json={"max_workers": 1, "with_report": False, "async_mode": True, "webhook_url": url2},
        )
        bid2 = r.json()["batch_id"]
        time.sleep(0.4)  # 约执行到第 ~13 条
        c = client.post(f"/api/projects/{pid}/execute/cancel", json={"batch_id": bid2})
        check(
            "B5-2-2 取消请求返回 ok",
            c.status_code == 200 and c.json().get("cancelled"),
            f"http={c.status_code}",
        )
        final2 = wait_state(client, pid, bid2, ("cancelled", "done"))
        for _ in range(50):
            if srv2.received:
                break
            time.sleep(0.1)
        check(
            "B5-2-2b webhook 回调 state=cancelled 且 done<total（未执行部分不丢）",
            len(srv2.received) == 1
            and srv2.received[0]["state"] == "cancelled"
            and srv2.received[0]["summary"]["total"] < 60,
            f"received={srv2.received}",
        )
    finally:
        executor._safe_run = orig
        srv2.shutdown()

    # ---------- B5-2-3 无 webhook 也不崩 ----------
    executor._safe_run = make_slow("pass", 0.02)
    try:
        client = TestClient(app)
        r = client.post(
            f"/api/projects/{pid}/execute",
            json={"max_workers": 1, "with_report": False, "async_mode": True},
        )
        bid3 = r.json()["batch_id"]
        final3 = wait_state(client, pid, bid3, ("done",))
        check(
            "B5-2-3 无 webhook_url 时 async 仍能 done（不崩）",
            final3 and final3["state"] == "done",
            f"state={final3['state'] if final3 else None}",
        )
    finally:
        executor._safe_run = orig

    # ---------- B5-2-4 P5-②1：cases.status 不被执行结果污染 ----------
    # 用一条真实同步执行（patched pass）后检查某 case
    executor._safe_run = make_slow("pass", 0.0)
    try:
        executor.run_project(pid, max_workers=1)
    finally:
        executor._safe_run = orig
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status, last_result FROM cases WHERE project_id=? LIMIT 1", (pid,))
    row = cur.fetchone()
    cur.execute("SELECT status FROM runs WHERE project_id=? LIMIT 1", (pid,))
    run_row = cur.fetchone()
    conn.close()
    check(
        "B5-2-4a 执行后 cases.status 仍为生命周期值(generated)，未被改为 pass",
        row["status"] == "generated",
        f"cases.status={row['status']}",
    )
    check(
        "B5-2-4b 执行结论冗余落到 cases.last_result=pass",
        row["last_result"] == "pass",
        f"cases.last_result={row['last_result']}",
    )
    check(
        "B5-2-4c 执行结论主存于 runs.status=pass（监控/趋势口径）",
        run_row["status"] == "pass",
        f"runs.status={run_row['status']}",
    )
    check(
        "B5-2-4d 语义解耦：cases.status 不在执行结果集合内（pass/fail/...）",
        row["status"]
        not in (
            "pass",
            "fail",
            "structural_only",
            "blocked_auth",
            "error",
            "skipped",
            "blocked_review",
        ),
        f"cases.status={row['status']}",
    )

    # ---------- B5-2-5 /execute/tasks 列出任务 ----------
    client = TestClient(app)
    tasks = client.get(f"/api/projects/{pid}/execute/tasks").json()
    bids = [t["batch_id"] for t in tasks.get("tasks", [])]
    check(
        "B5-2-5 /execute/tasks 列出已结束任务（含本轮 batch）",
        any(b in bids for b in (bid, bid2, bid3)),
        f"tasks_count={len(bids)}",
    )

    passed = sum(1 for _, ok, _ in _results if ok)
    print("\n" + "=" * 60)
    print(
        f"==== 阶段5 批次1（P5-★4 + P5-②1）自测汇总：{passed}/{len(_results)} 通过，"
        f"耗时 {time.time() - t0:.1f}s ===="
    )
    for name, ok, detail in _results:
        if not ok:
            print(f"  [FAILED] {name} — {detail}")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
