"""阶段6 批次1 自测：P6-★1 双向追溯 / P6-★2 证据 / P6-★3 单条报告端点 / P6-★4 失败归因。

不依赖被测服务；用进程内 SQLite + 合成用例与执行结果，直接驱动 reporter 与
FastAPI TestClient，覆盖：
  P6-★1 明细含 tp_id / fp_contract_id / source，summary.traceability 覆盖率=100%
  P6-★2 失败/浏览器用例渲染截图链接（file://）与日志详情
  P6-★3 GET /reports/{rid} 与 /reports/{rid}/html 可程序化取回
  P6-★4 summary.failures（by_status / by_module / clusters）+ 报告含失败归因卡片
退出码 0 = 全绿。
"""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import get_conn
from backend.main import app
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


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


def setup_project(name):
    existing = pm.find_by_name(name)
    pid = (
        existing["id"]
        if existing
        else pm.add(name=name, local_path="work/targets/_selftest", ptype="pc")
    )
    conn = get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points", "reports"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()
    return pid


def add_tp_and_case(
    pid, tp_id, title, module, source, ctype="api", status="generated", fp_cid="fp_X"
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
            fp_cid,
            "正常",
            module,
            "语义",
            title,
            source,
            "GET",
            "/x",
            "route_defined",
            "正常",
            "全量",
            "approved",
        ),
    )
    cur.execute(
        """INSERT INTO cases
           (project_id, tp_id, fp_contract_id, title, module, ctype, status,
            review_status, test_type)
           VALUES (?,?,?,?,?,?,'generated','approved','全量')""",
        (pid, tp_id, fp_cid, title, module, ctype),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def cleanup(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT html_path FROM reports WHERE project_id=?", (pid,))
    for r in cur.fetchall():
        p = r["html_path"]
        if p and Path(p).exists():
            try:
                Path(p).unlink()
            except Exception:
                pass
    for tbl in ("runs", "cases", "test_points", "functional_points", "reports"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def test_p6():
    pid = setup_project("selftest_b6_1")
    client = TestClient(app)
    try:
        # 3 个用例：分别 api/pass、api/fail(带截图)、page/structural_only
        cid1 = add_tp_and_case(pid, "TP-1", "登录接口", "用户模块", "backend/user.py", ctype="api")
        cid2 = add_tp_and_case(pid, "TP-2", "订单创建", "订单模块", "backend/order.py", ctype="api")
        cid3 = add_tp_and_case(
            pid, "TP-3", "首页渲染", "前端模块", "frontend/home.vue", ctype="page"
        )

        results = [
            {
                "case_id": cid1,
                "ctype": "api",
                "status": "pass",
                "reason": "路由存在且动态通过",
                "log": "dynamic=200",
            },
            {
                "case_id": cid2,
                "ctype": "api",
                "status": "fail",
                "reason": "期望 2xx，实际 500",
                "log": "dynamic=500 trace=NullPtr",
                "screenshot_path": "C:/tmp/fail_order.png",
            },
            {
                "case_id": cid3,
                "ctype": "page",
                "status": "structural_only",
                "reason": "路由存在（静态断言），未做真实渲染",
                "log": "static only",
            },
        ]

        rep = reporter.build(
            pid, results, meta={"project": "selftest_b6_1", "batch_id": "run_b6_demo"}
        )
        summary = rep["summary"]
        rid = rep["id"]

        # ---- P6-★1 双向追溯 ----
        tr = summary.get("traceability", {})
        enriched_ok = tr.get("enriched") == 3 and tr.get("coverage") == 100.0
        check("P6-★1-1 summary.traceability 覆盖 3/3（100%）", enriched_ok, f"trace={tr}")

        # 明细行被挂上 tp_id/fp_contract_id/source
        r1 = next(r for r in results if r["case_id"] == cid1)
        r2 = next(r for r in results if r["case_id"] == cid2)
        check(
            "P6-★1-2 结果关联到 tp_id/fp_contract_id/source",
            r1.get("tp_id") == "TP-1"
            and r1.get("fp_contract_id") == "fp_X"
            and r1.get("source") == "backend/user.py"
            and r2.get("tp_id") == "TP-2",
            f"tp={r1.get('tp_id')} src={r1.get('source')}",
        )

        html = Path(rep["html_path"]).read_text(encoding="utf-8")
        check(
            "P6-★1-3 HTML 明细呈现 测试点/功能点/源码 列与值",
            "TP-1" in html
            and "fp_X" in html
            and "backend/order.py" in html
            and "源码" in html
            and "测试点" in html,
            "html 含追溯信息",
        )

        # ---- P6-★2 证据 ----
        check(
            "P6-★2-1 失败用例截图渲染为 file:// 链接",
            "file:///C:/tmp/fail_order.png" in html,
            "截图链接出现在 html",
        )
        check(
            "P6-★2-2 明细含日志详情(details 折叠)",
            "<details>" in html and "dynamic=500" in html,
            "日志详情渲染",
        )

        # ---- P6-★4 失败归因 ----
        fl = summary.get("failures", {})
        check(
            "P6-★4-1 summary.failures.by_status 含 fail/structural_only",
            fl.get("by_status", {}).get("fail") == 1
            and fl.get("by_status", {}).get("structural_only") == 1
            and fl.get("total_problem") == 2,
            f"by_status={fl.get('by_status')}",
        )
        check(
            "P6-★4-2 失败聚类含 模块×状态 与样例 case_id",
            any(
                c["module"] == "订单模块" and c["status"] == "fail" and cid2 in c["samples"]
                for c in fl.get("clusters", [])
            ),
            f"clusters={fl.get('clusters')}",
        )
        check(
            "P6-★4-3 summary.by_module 含通过率",
            "订单模块" in summary.get("by_module", {})
            and summary["by_module"]["订单模块"]["pass_rate"] == 0.0,
            f"by_module={summary.get('by_module')}",
        )
        check(
            "P6-★4-4 HTML 含失败归因卡片", "失败归因" in html and "失败聚类" in html, "归因卡片渲染"
        )

        # ---- P6-★3 单条报告端点 ----
        resp = client.get(f"/api/projects/{pid}/reports/{rid}")
        check(
            "P6-★3-1 GET /reports/{rid} 返回 ok + summary",
            resp.status_code == 200
            and resp.json().get("ok")
            and "failures" in resp.json().get("summary", {}),
            f"status={resp.status_code}",
        )
        resp_in = client.get(f"/api/projects/{pid}/reports/{rid}?inline=true")
        jin = resp_in.json()
        check(
            "P6-★3-2 inline=true 一并返回 HTML 全文",
            resp_in.status_code == 200 and "<html" in (jin.get("html") or ""),
            f"html_len={len(jin.get('html') or '')}",
        )
        resp_html = client.get(f"/api/projects/{pid}/reports/{rid}/html")
        check(
            "P6-★3-3 GET /reports/{rid}/html 返回 HTML 文件",
            resp_html.status_code == 200
            and "text/html" in resp_html.headers.get("content-type", ""),
            f"ct={resp_html.headers.get('content-type')}",
        )
        # 不存在的报告 → 优雅 404
        resp_missing = client.get(f"/api/projects/{pid}/reports/999999")
        check(
            "P6-★3-4 不存在的报告返回 ok=false（不崩溃）",
            resp_missing.status_code == 200 and resp_missing.json().get("ok") is False,
            f"body={resp_missing.json()}",
        )

        # 报告行确已落库（reports 表）
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) c FROM reports WHERE project_id=?", (pid,))
        nrep = cur.fetchone()["c"]
        conn.close()
        check("P6-★3-5 报告已写入 reports 表", nrep >= 1, f"reports={nrep}")
    finally:
        cleanup(pid)


if __name__ == "__main__":
    print("=== 阶段6 批次1（P6-★1~★4）自测 ===")
    test_p6()
    print("\n" + "=" * 60)
    print(f"结果：PASS {PASS} / FAIL {FAIL}")
    print("=" * 60)
    for line in LOG:
        if line.startswith("[FAIL]"):
            print(line)
    raise SystemExit(0 if FAIL == 0 else 1)
