"""阶段4 批次3 自测：D-★6（执行子集筛选）/ D-②1（鉴权态复用）/ D-②2（并发执行）。

验证项
 B4-3-1  按 priority 筛选：执行条数与 DB 命中条数一致，且不漏不串
 B4-3-2  按 test_type 筛选：全量/新增 可分别执行（昨天落地的字段在执行侧生效）
 B4-3-3  按 ids / module 筛选：结果集合精确
 B4-3-4  未知筛选字段 → ValueError（防脏列名进 SQL）
 B4-3-5  端点 /execute + /filter_options 可用且口径一致
 B4-3-6  D-②1 带鉴权态：受保护接口 200 → pass（不再是 blocked_auth）
 B4-3-7  D-②1 无凭据：受保护接口 → blocked_auth（既不算通过也不算失败）
 B4-3-8  D-②1 token 失效：401 后自动刷新并仅重试一次 → 恢复 pass
 B4-3-9  D-②2 并发与串行结果完全一致（case_id → status 映射相同）
 B4-3-10 D-②2 并发确实更快（IO 密集场景耗时显著下降）
 B4-3-11 D-②2 并发下 runs 落库数 == 执行条数（写库串行，无丢失）
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

import backend.db as db
from backend.config import PROJECT_ROOT, settings
from backend.main import _analyze_project, app
from backend.modules import auth, tp_store
from backend.modules.case_generator import case_generator
from backend.modules.executor import executor
from backend.modules.project_manager import pm


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# ======================= mock 被测服务 =======================
STATE = {"valid": "tok_v1", "issued": 0, "seen_auth": []}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=b"{}"):
        raw = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/health", "/api/v1/health"):
            return self._send(200, b'{"status":"ok"}')
        if self.path == "/open":
            return self._send(200, b'{"ok":true}')
        if self.path == "/secret":
            STATE["seen_auth"].append(self.headers.get("Authorization", ""))
            if self.headers.get("Authorization", "") == "Bearer " + STATE["valid"]:
                return self._send(200, b'{"ok":true}')
            return self._send(401, b'{"detail":"unauthorized"}')
        return self._send(404, b'{"detail":"not found"}')

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        if self.path.endswith("/auth/unified-login") or self.path.endswith("/auth/login"):
            try:
                body = json.loads(raw or b"{}")
            except Exception:
                body = {}
            if body.get("password"):
                STATE["issued"] += 1
                return self._send(200, json.dumps({"access_token": STATE["valid"]}).encode())
            return self._send(401, b'{"detail":"bad credentials"}')
        return self._send(404, b"{}")


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading_target = None
import threading


threading.Thread(target=srv.serve_forever, daemon=True).start()
MOCK = f"http://127.0.0.1:{port}"


def _step(path, method="GET", expect="功能可用"):
    return json.dumps(
        [
            {
                "action": "http_probe",
                "method": method,
                "path": path,
                "file": "backend/research-agent-source/server.py",
                "expect": expect,
            }
        ],
        ensure_ascii=False,
    )


def make_mock_project(name, base):
    """建一个只含 3 条用例的 mock 项目（2 条 API + 1 条 page）。"""
    p = pm.find_by_name(name)
    if p:
        pid = p["id"]
    else:
        pid = pm.add(name=name, local_path=str(TARGET), ptype="pc", base_url=base)
    # 复用旧项目时必须刷新 base_url：mock 端口每轮随机，沿用上一轮的会指向死端口
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET base_url=? WHERE id=?", (base, pid))
    cur.execute("DELETE FROM cases WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM runs WHERE project_id=?", (pid,))
    for title, path in (("开放接口", "/open"), ("受保护接口", "/secret")):
        cur.execute(
            """INSERT INTO cases (project_id, title, steps, ctype, status,
                                  review_status, priority, module, case_type, test_type)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (pid, title, _step(path), "api", "generated", "approved", "P1", "鉴权", "正常", "全量"),
        )
    conn.commit()
    conn.close()
    return pid


def main():
    t0 = time.time()
    db.init_db()
    if not pm.find_by_name("research-agent"):
        pm.add(
            name="research-agent",
            local_path=str(TARGET),
            type="pc",
            base_url="http://localhost:8010",
        )
    pid = pm.find_by_name("research-agent")["id"]

    conn = db.get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()

    _analyze_project(pid)
    tp_store.import_test_points(pid)
    n = case_generator.generate_for_project(pid)
    # generate_for_project 现返回对账统计 dict（C-②8）；active 为本轮生效用例数
    total_cases = n.get("active", 0)
    assert isinstance(n, dict) and total_cases >= 1, f"expected active>=1, got {n}"
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cases SET review_status='approved' WHERE project_id=? AND status!='archived'",
        (pid,),
    )
    conn.commit()
    conn.close()
    print(f"[setup] 真实项目 {pid}：{total_cases} 条用例（已全部审核通过）")

    # ---------- B4-3-1 按 priority 筛选 ----------
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND priority=?", (pid, "P1"))
    p1_total = cur.fetchone()["c"]
    conn.close()
    r_p1 = executor.run_project(pid, filters={"priority": "P1"}, max_workers=1)
    check(
        "B4-3-1 按 priority 筛选：执行条数 == DB 中 P1 条数",
        len(r_p1) == p1_total == executor.last_meta["requested"],
        f"executed={len(r_p1)}, db_p1={p1_total}",
    )

    # ---------- B4-3-2 按 test_type 筛选 ----------
    r_all = executor.run_project(pid, filters={"test_type": "全量"}, max_workers=1)
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cases SET test_type='新增' WHERE project_id=? "
        "AND id IN (SELECT id FROM cases WHERE project_id=? "
        "AND status!='archived' ORDER BY id LIMIT 12)",
        (pid, pid),
    )
    conn.commit()
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND test_type='新增'", (pid,))
    new_total = cur.fetchone()["c"]
    conn.close()
    r_new = executor.run_project(pid, filters={"test_type": "新增"}, max_workers=1)
    check(
        "B4-3-2 按 test_type 筛选：全量扫描全部用例、增量子集 12 条可分别执行",
        len(r_all) == total_cases and len(r_new) == new_total == 12,
        f"全量={len(r_all)}, 新增={len(r_new)} (db={new_total})",
    )

    # ---------- B4-3-3 按 ids / module 筛选 ----------
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM cases WHERE project_id=? AND status!='archived' ORDER BY id LIMIT 5", (pid,)
    )
    some_ids = [r["id"] for r in cur.fetchall()]
    cur.execute(
        "SELECT module, COUNT(*) c FROM cases WHERE project_id=? "
        "AND status!='archived' GROUP BY module ORDER BY c DESC LIMIT 1",
        (pid,),
    )
    row = cur.fetchone()
    top_module, mod_total = row["module"], row["c"]
    conn.close()
    r_ids = executor.run_project(pid, filters={"ids": some_ids}, max_workers=1)
    r_mod = executor.run_project(pid, filters={"module": top_module}, max_workers=1)
    check(
        "B4-3-3 按 ids 筛选：结果集合与传入 id 完全一致",
        sorted(x["case_id"] for x in r_ids) == sorted(some_ids),
        f"got={sorted(x['case_id'] for x in r_ids)}",
    )
    check(
        "B4-3-3b 按 module 筛选：执行条数 == 该模块用例数",
        len(r_mod) == mod_total,
        f"module={top_module}, executed={len(r_mod)}/{mod_total}",
    )

    # ---------- B4-3-4 未知字段 ----------
    raised = ""
    try:
        executor.run_project(pid, filters={"drop_table": "x"}, max_workers=1)
    except ValueError as e:
        raised = str(e)
    check(
        "B4-3-4 未知筛选字段被拒绝（防脏列名拼进 SQL）", "不支持的筛选字段" in raised, raised[:60]
    )

    # ---------- B4-3-5 端点 ----------
    client = TestClient(app)
    resp = client.post(
        f"/api/projects/{pid}/execute",
        json={"filters": {"priority": ["P1"]}, "max_workers": 1, "with_report": False},
    )
    body = resp.json()
    check(
        "B4-3-5 POST /execute 端点可用且执行条数正确（不生成报告）",
        resp.status_code == 200 and body.get("executed") == p1_total,
        f"http={resp.status_code}, executed={body.get('executed')}",
    )
    opt = client.get(f"/api/projects/{pid}/filter_options").json()
    dims = opt.get("dimensions", {})
    check(
        "B4-3-5b GET /filter_options 返回可用维度与分布",
        opt.get("total") == total_cases
        and any(d["value"] == "P1" for d in dims.get("priority", []))
        and {"新增", "全量"} <= {d["value"] for d in dims.get("test_type", [])},
        f"total={opt.get('total')}, test_type={dims.get('test_type')}",
    )

    # ======================= D-②1 鉴权态复用 =======================
    mpid = make_mock_project("b43-mock", MOCK)
    settings.ENABLE_DYNAMIC_PROBE = True
    settings.RA_ACCOUNT, settings.RA_PASSWORD = "tester", "secret"
    settings.RA_OTP = ""
    settings.RA_AUTH_TOKEN = ""
    auth.invalidate()
    mock_proj = pm.get(mpid)

    r_auth = executor.run_project(mpid, max_workers=1)
    by_title = {}
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM cases WHERE project_id=?", (mpid,))
    titles = {r["id"]: r["title"] for r in cur.fetchall()}
    conn.close()
    for r in r_auth:
        by_title[titles.get(r["case_id"], "?")] = r
    check(
        "B4-3-6 D-②1 带鉴权态：受保护接口拿到 200 → pass（不再是 blocked_auth）",
        by_title.get("受保护接口", {}).get("status") == "pass",
        f"status={by_title.get('受保护接口', {}).get('status')}, "
        f"reason={by_title.get('受保护接口', {}).get('reason')}",
    )
    check(
        "B4-3-6b 开放接口无需鉴权也正常判定", by_title.get("开放接口", {}).get("status") == "pass"
    )

    # 无凭据
    settings.RA_ACCOUNT, settings.RA_PASSWORD = "", ""
    auth.invalidate()
    r_noauth = executor.run_project(mpid, max_workers=1)
    st = {titles.get(r["case_id"], "?"): r["status"] for r in r_noauth}
    check(
        "B4-3-7 D-②1 无凭据：受保护接口 → blocked_auth（不算通过也不算失败）",
        st.get("受保护接口") == "blocked_auth",
        f"status={st}",
    )

    # token 轮换 → 自动刷新
    settings.RA_ACCOUNT, settings.RA_PASSWORD = "tester", "secret"
    auth.invalidate()
    executor.run_project(mpid, max_workers=1)  # 先缓存 tok_v1
    STATE["valid"] = "tok_v2"  # 服务端轮换，缓存 token 失效
    r_rot = executor.run_project(mpid, max_workers=1)
    rot = {titles.get(r["case_id"], "?"): r for r in r_rot}
    check(
        "B4-3-8 D-②1 token 失效后自动刷新并重试一次 → 恢复 pass",
        rot.get("受保护接口", {}).get("status") == "pass"
        and rot.get("受保护接口", {}).get("auth") == "refreshed",
        f"status={rot.get('受保护接口', {}).get('status')}, "
        f"auth={rot.get('受保护接口', {}).get('auth')}, 登录次数={STATE['issued']}",
    )

    # ======================= D-②2 并发 =======================
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM cases WHERE project_id=? AND status!='archived' ORDER BY id LIMIT 120",
        (pid,),
    )
    sub_ids = [r["id"] for r in cur.fetchall()]
    conn.close()
    f = {"ids": sub_ids}
    r_ser = executor.run_project(pid, filters=f, max_workers=1)
    bid_ser = executor.last_batch_id
    r_par = executor.run_project(pid, filters=f, max_workers=8)
    bid_par = executor.last_batch_id
    m_ser = {r["case_id"]: r["status"] for r in r_ser}
    m_par = {r["case_id"]: r["status"] for r in r_par}
    check(
        "B4-3-9 D-②2 并发与串行结果完全一致（逐条 case_id→status 相同）",
        m_ser == m_par and len(m_par) == 120,
        f"serial={len(m_ser)}, parallel={len(m_par)}",
    )

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid_par))
    runs_par = cur.fetchone()["c"]
    conn.close()
    check(
        "B4-3-11 D-②2 并发下 runs 落库数 == 执行条数（写库串行无丢失）",
        runs_par == 120 == len(r_par),
        f"runs={runs_par}",
    )

    orig_rc = executor._run_case

    def slow(c, proj, service_up, ctx=None):
        time.sleep(0.02)
        return orig_rc(c, proj, service_up, ctx)

    executor._run_case = slow
    try:
        t1 = time.time()
        executor.run_project(pid, filters=f, max_workers=1)
        t_ser = time.time() - t1
        t2 = time.time()
        executor.run_project(pid, filters=f, max_workers=8)
        t_par = time.time() - t2
    finally:
        executor._run_case = orig_rc
    check(
        "B4-3-10 D-②2 并发确实更快（120 条 ×20ms 人工延迟）",
        t_par < t_ser * 0.6,
        f"串行={t_ser:.2f}s, 并发(8)={t_par:.2f}s, 提速={t_ser / max(t_par, 0.001):.1f}x",
    )

    settings.ENABLE_DYNAMIC_PROBE = False
    srv.shutdown()

    passed = sum(1 for _, ok, _ in _results if ok)
    print("\n" + "=" * 60)
    print(f"==== 批次3 自测汇总：{passed}/{len(_results)} 通过，耗时 {time.time() - t0:.1f}s ====")
    for name, ok, detail in _results:
        if not ok:
            print(f"  [FAILED] {name} — {detail}")
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
