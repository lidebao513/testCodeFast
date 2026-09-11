"""阶段5 批次2 自测：P5-②5 进度持久化 + C-②8 增量对账。

不依赖被测服务运行；用进程内 SQLite + 合成数据，直接驱动 executor / case_generator /
batch_store，覆盖：
  P5-②5-1 register→update→finish 全部落 run_batches 表
  P5-②5-2 get_batch_status 在 registry 缺失时回退 DB（live=False, source=run_batches）
  P5-②5-3 recover_interrupted 把 DB 中 running 批次标 interrupted 并触发 webhook
  C-②8-1 首轮生成：全部 generated
  C-②8-2 删1改1后重生：reused / obsolete / updated 三类正确
  C-②8-3 执行排除 obsolete；export 排除 obsolete；复活后回到 generated
退出码 0 = 全绿。
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from backend.db import get_conn
from backend.modules import batch_store as bs_mod
from backend.modules.case_generator import case_generator
from backend.modules.executor import executor
from backend.modules.project_manager import pm


PASS = 0
FAIL = 0
LOG = []


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        LOG.append(f"[PASS] {name} {detail}")
    else:
        FAIL += 1
        LOG.append(f"[FAIL] {name} {detail}")
    print(("✅ " if ok else "❌ ") + name + (f" — {detail}" if detail else ""))


# ---------- 准备测试项目（合成数据，不依赖真实仓库） ----------
def setup_project(name):
    existing = pm.find_by_name(name)
    if existing:
        pid = existing["id"]
    else:
        pid = pm.add(name=name, local_path="work/targets/_selftest", ptype="pc")
    conn = get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()
    return pid


def add_tp(
    pid,
    tp_id,
    title,
    category="正常",
    method="GET",
    area="/x",
    source="a.py",
    expect="route_defined",
    module="M",
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO test_points
           (project_id, tp_id, fp_contract_id, category, module, semantic, title,
            source, method, area, expect, dimension, tag, review_status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            pid,
            tp_id,
            None,
            category,
            module,
            "语义",
            title,
            source,
            method,
            area,
            expect,
            "正常",
            "全量",
            "approved",
        ),
    )
    conn.commit()
    conn.close()


def case_statuses(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tp_id, status FROM cases WHERE project_id=? ORDER BY tp_id", (pid,))
    rows = {r["tp_id"]: r["status"] for r in cur.fetchall()}
    conn.close()
    return rows


def cleanup(pid):
    conn = get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM run_batches WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# ================= P5-②5 =================
def test_p5_25():
    pid = setup_project("selftest_b5_3_persist")
    try:
        bid = f"run_{pid}_persist_1"
        # 1) register + update + finish 全落库
        executor.register_batch(bid, pid, 10, {"priority": ["P1"]}, webhook_url="")
        for s in ("pass", "pass", "fail"):
            executor.update_progress(bid, s)
        executor.finish_batch(bid, state="done")
        row = bs_mod.get(bid)
        check(
            "P5-②5-1 register/update/finish 落 run_batches 表",
            row is not None
            and row["total"] == 10
            and row["done"] == 3
            and row["state"] == "done"
            and row["status_counts"].get("pass") == 2
            and row["status_counts"].get("fail") == 1,
            f"row={row['state']} done={row['done']} counts={row['status_counts']}",
        )

        # 2) registry 缺失 → 回退 DB（live=False, source=run_batches）
        bid2 = f"run_{pid}_persist_2"
        bs_mod.upsert(bid2, pid, 5, {"module": ["M"]}, state="done")
        bs_mod.inc_progress(bid2, "pass")
        bs_mod.set_state(bid2, "done")
        st = executor.get_batch_status(bid2)  # 不在 registry，应回退 DB
        check(
            "P5-②5-2 get_batch_status 回退 DB（live=False）",
            st is not None
            and st.get("live") is False
            and st["state"] == "done"
            and st["total"] == 5
            and st["status_counts"].get("pass") == 1,
            f"live={st.get('live')} state={st.get('state')}",
        )

        # 3) recover_interrupted：running 批次 → interrupted + webhook 触发
        received = {}

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                ln = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(ln)
                try:
                    received.update(json.loads(body or b"{}"))
                except Exception:
                    pass
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            wh = f"http://127.0.0.1:{port}/hook"
            bid3 = f"run_{pid}_persist_3"
            bs_mod.upsert(bid3, pid, 8, {}, webhook_url=wh, state="running")
            rec = bs_mod.recover_interrupted(executor.fire_webhook)
            time.sleep(0.3)
            row3 = bs_mod.get(bid3)
            check(
                "P5-②5-3 recover 将 running 标 interrupted 且 webhook 触发",
                bid3 in rec
                and row3["state"] == "interrupted"
                and received.get("state") == "interrupted"
                and received.get("batch_id") == bid3,
                f"row_state={row3['state']} recv={received.get('state')}",
            )
        finally:
            srv.shutdown()
            srv.server_close()
    finally:
        cleanup(pid)


# ================= C-②8 =================
def test_c28():
    pid = setup_project("selftest_b5_3_reconcile")
    try:
        # 首轮：3 个 TP
        add_tp(pid, "TP-A", "用例A", module="MA")
        add_tp(pid, "TP-B", "用例B", module="MB")
        add_tp(pid, "TP-C", "用例C", module="MC", expect="route_defined")
        stats = case_generator.generate_for_project(pid)
        st1 = case_statuses(pid)
        check(
            "C-②8-1 首轮生成全部为 generated",
            st1 == {"TP-A": "generated", "TP-B": "generated", "TP-C": "generated"}
            and stats["created"] == 3
            and stats["active"] == 3,
            f"statuses={st1} stats={stats}",
        )

        # 代码变更：删 TP-B（功能点废弃），改 TP-C 的 expect（用例被修订）
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM test_points WHERE project_id=? AND tp_id='TP-B'", (pid,))
        cur.execute(
            "UPDATE test_points SET expect='→ 404' WHERE project_id=? AND tp_id='TP-C'", (pid,)
        )
        conn.commit()
        conn.close()

        stats2 = case_generator.generate_for_project(pid)
        st2 = case_statuses(pid)
        check(
            "C-②8-2 删1改1后：TP-A reused / TP-B obsolete / TP-C updated",
            st2.get("TP-A") == "generated"
            and st2.get("TP-B") == "obsolete"
            and st2.get("TP-C") == "updated"
            and stats2["reused"] == 1
            and stats2["obsolete"] == 1
            and stats2["updated"] == 1
            and stats2["created"] == 0
            and stats2["active"] == 2,
            f"statuses={st2} stats={stats2}",
        )

        # 执行排除 obsolete：TP-B 不被选入执行
        cases, _ = executor.select_cases(pid, include_archived=False)
        sel_ids = {c.get("tp_id") for c in cases}
        check(
            "C-②8-3 执行选择器排除 obsolete（TP-B 不入选）",
            "TP-B" not in sel_ids and "TP-A" in sel_ids and "TP-C" in sel_ids,
            f"selected_tp={sorted(x for x in sel_ids if x)}",
        )

        # export 排除 obsolete：导出清册不含 TP-B
        exp = case_generator.export_test_cases(pid)
        with open(exp["json_path"], encoding="utf-8") as f:
            catalog = json.load(f).get("cases", [])
        exported_tp = {c["tp_id"] for c in catalog}
        check(
            "C-②8-4 交付物导出排除 obsolete（TP-B 不出现）",
            "TP-B" not in exported_tp and exp["count"] == 2,
            f"exported={sorted(x for x in exported_tp if x)} count={exp['count']}",
        )

        # 复活：TP-B 重新出现 → 回到 generated（不堆积新行）
        add_tp(pid, "TP-B", "用例B", module="MB")
        stats3 = case_generator.generate_for_project(pid)
        st3 = case_statuses(pid)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=?", (pid,))
        cnt = cur.fetchone()["c"]
        conn.close()
        check(
            "C-②8-5 废弃用例复活回到 generated（无行堆积）",
            st3.get("TP-B") == "generated"
            and cnt == 3
            and stats3["reused"] >= 1
            and stats3["created"] == 0,
            f"statuses={st3} total_rows={cnt} stats={stats3}",
        )
    finally:
        cleanup(pid)


if __name__ == "__main__":
    print("=== P5-②5 + C-②8 自测 ===")
    test_p5_25()
    test_c28()
    print("\n" + "=" * 60)
    print(f"结果：PASS {PASS} / FAIL {FAIL}")
    print("=" * 60)
    for line in LOG:
        if line.startswith("[FAIL]"):
            print(line)
    raise SystemExit(0 if FAIL == 0 else 1)
