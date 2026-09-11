"""阶段6 批次2 自测：P6-②1 趋势/flaky + P6-②2 覆盖率报告。

不依赖被测服务；用进程内 SQLite + 合成 FP/TP/Case/多批次 runs，直接驱动
analytics 模块与 FastAPI TestClient，覆盖：
  P6-②1 趋势：多批次 pass_rate 序列 + 方向判定
  P6-②1 flaky：跨批次结果不一致用例识别（含经典 flaky vs 环境态不一致区分）
  P6-②2 覆盖率：用例/测试点/功能点 三级覆盖 + 未覆盖缺口定位
  API：/reports/trend、/reports/flaky、/coverage、/reports/trend_coverage
退出码 0 = 全绿。
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.db import get_conn
from backend.main import app
from backend.modules import analytics as analytics_module
from backend.modules import batch_store as bs
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


def setup_project(name):
    existing = pm.find_by_name(name)
    pid = (
        existing["id"]
        if existing
        else pm.add(name=name, local_path="work/targets/_selftest", ptype="pc")
    )
    conn = get_conn()
    cur = conn.cursor()
    for tbl in (
        "runs",
        "cases",
        "test_points",
        "functional_points",
        "reports",
        "run_batches",
        "change_log",
    ):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    conn.close()
    return pid


def add_fp(pid, cid, name, module, ftype="api"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO functional_points
           (project_id, commit_ref, file_path, name, description, ftype,
            contract_id, review_status, title, module)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (pid, "abc123", "src/x.py", name, name, ftype, cid, "approved", name, module),
    )
    fid = cur.lastrowid
    conn.commit()
    conn.close()
    return fid


def add_tp(pid, tp_id, fp_cid, title, module):
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
            "src/x.py",
            "GET",
            "/x",
            "route_defined",
            "正常",
            "全量",
            "approved",
        ),
    )
    conn.commit()
    conn.close()


def add_case(pid, tp_id, fp_cid, title, module):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cases
           (project_id, tp_id, fp_contract_id, title, module, ctype, status,
            review_status, test_type)
           VALUES (?,?,?,?,?,?,'generated','approved','全量')""",
        (pid, tp_id, fp_cid, title, module, "api"),
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def add_run(pid, case_id, batch_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO runs (project_id, case_id, status, batch_id)
           VALUES (?,?,?,?)""",
        (pid, case_id, status, batch_id),
    )
    conn.commit()
    conn.close()


def seed_batch(pid, bid, sc):
    bs.upsert(bid, pid, total=sum(sc.values()), filters={}, webhook_url="", state="done")
    for s, c in sc.items():
        for _ in range(c):
            pass
    # 直接覆盖 status_counts（upsert 写入空计数，这里精确写入）
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE run_batches SET status_counts=?, state='done' WHERE batch_id=?",
        (json.dumps(sc, ensure_ascii=False), bid),
    )
    conn.commit()
    conn.close()


def cleanup(pid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT html_path FROM reports WHERE project_id=?", (pid,))
    for r in cur.fetchall():
        p = r["html_path"]
        if p and "trend_coverage" in (p or "") and Path(p).exists():
            try:
                Path(p).unlink()
            except Exception:
                pass
    for tbl in (
        "runs",
        "cases",
        "test_points",
        "functional_points",
        "reports",
        "run_batches",
        "change_log",
    ):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    cur.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def test_b6_2():
    pid = setup_project("selftest_b6_2")
    client = TestClient(app)
    try:
        # ---- 功能点：5 个，其中 fp_E 不挂任何测试点（制造 FP 缺口）----
        add_fp(pid, "fp_A", "查询用户", "用户模块")
        add_fp(pid, "fp_B", "创建订单", "订单模块")
        add_fp(pid, "fp_C", "导出报表", "报表模块")
        add_fp(pid, "fp_D", "删除缓存", "缓存模块")
        add_fp(pid, "fp_E", "未测功能", "其它模块")  # 无 TP

        # ---- 测试点：5 个；TP5→fp_D 但故意不给用例（制造 TP 缺口）----
        add_tp(pid, "TP-1", "fp_A", "查询用户-正常", "用户模块")
        add_tp(pid, "TP-2", "fp_A", "查询用户-异常", "用户模块")
        add_tp(pid, "TP-3", "fp_B", "创建订单-正常", "订单模块")
        add_tp(pid, "TP-4", "fp_C", "导出报表-正常", "报表模块")
        add_tp(pid, "TP-5", "fp_D", "删除缓存-正常", "缓存模块")  # 无 case

        # ---- 用例：覆盖 TP1~TP4，不覆盖 TP5 ----
        c1 = add_case(pid, "TP-1", "fp_A", "查询用户-正常", "用户模块")
        c2 = add_case(pid, "TP-2", "fp_A", "查询用户-异常", "用户模块")
        c3 = add_case(pid, "TP-3", "fp_B", "创建订单-正常", "订单模块")
        c4 = add_case(pid, "TP-4", "fp_C", "导出报表-正常", "报表模块")

        # ---- 两个批次的 runs（构造 flaky 与不一致）----
        # batch_A: c1=pass, c2=pass, c3=fail, c4=structural_only
        add_run(pid, c1, "B_A", "pass")
        add_run(pid, c2, "B_A", "pass")
        add_run(pid, c3, "B_A", "fail")
        add_run(pid, c4, "B_A", "structural_only")
        # batch_B: c1=pass, c2=fail(flaky!), c3=error(不一致非flaky), 无 c4
        add_run(pid, c1, "B_B", "pass")
        add_run(pid, c2, "B_B", "fail")
        add_run(pid, c3, "B_B", "error")

        seed_batch(pid, "B_A", {"pass": 1, "fail": 2, "structural_only": 1})
        seed_batch(pid, "B_B", {"pass": 1, "fail": 1, "error": 1})

        # ================= 趋势（P6-②1） =================
        tr = analytics_module.trend(pid)
        check("P6-②1-1 趋势含 2 个批次点", tr["count"] == 2, f"count={tr['count']}")
        rates = [p["pass_rate"] for p in tr["points"]]
        check("P6-②1-2 每批次算出 pass_rate", all(r is not None for r in rates), f"rates={rates}")
        check(
            "P6-②1-3 方向判定为改善（33%→50%）",
            tr["pass_rate_direction"] == "improving",
            f"dir={tr['pass_rate_direction']}",
        )
        # 端点
        r_trend = client.get(f"/api/projects/{pid}/reports/trend")
        check(
            "P6-②1-4 GET /reports/trend 返回 2 点",
            r_trend.status_code == 200 and r_trend.json()["count"] == 2,
            f"status={r_trend.status_code}",
        )

        # ================= flaky（P6-②1） =================
        fl = analytics_module.flaky(pid)
        check(
            "P6-②1-5 检测到 1 条经典 flaky（c2: pass↔fail）",
            fl["flaky_count"] == 1 and fl["flaky"][0]["case_id"] == c2,
            f"flaky={fl['flaky_count']} ids={[c['case_id'] for c in fl['flaky']]}",
        )
        # c3 fail↔error（无 pass）应判为不一致但非经典 flaky
        inc_ids = [c["case_id"] for c in fl["inconsistent_nonflaky"]]
        check(
            "P6-②1-6 fail↔error（无 pass）判为不一致非 flaky",
            c3 in inc_ids and c3 not in [c["case_id"] for c in fl["flaky"]],
            f"inconsistent={inc_ids}",
        )
        # c1 两批都 pass → 不 flaky 不 inconsistent
        check(
            "P6-②1-7 两批一致(pass↔pass)不计入",
            c1 not in [c["case_id"] for c in fl["flaky"]] and c1 not in inc_ids,
            "c1 判为稳定",
        )
        r_flaky = client.get(f"/api/projects/{pid}/reports/flaky")
        check(
            "P6-②1-8 GET /reports/flaky 返回 flaky_count=1",
            r_flaky.status_code == 200 and r_flaky.json()["flaky_count"] == 1,
            f"status={r_flaky.status_code}",
        )

        # ================= 覆盖率（P6-②2） =================
        cov = analytics_module.coverage(pid)
        # FP: 5 个，fp_E 无 TP → 覆盖 4 → 80%
        check(
            "P6-②2-1 功能点覆盖率 80%（5 中 4 有 TP）",
            cov["fp_total"] == 5 and cov["fp_covered"] == 4 and cov["fp_rate"] == 80.0,
            f"fp={cov['fp_total']} cov={cov['fp_covered']} rate={cov['fp_rate']}",
        )
        # TP: 5 个，TP5 无 case → 覆盖 4 → 80%
        check(
            "P6-②2-2 测试点覆盖率 80%（5 中 4 有 case）",
            cov["tp_total"] == 5 and cov["tp_covered"] == 4 and cov["tp_rate"] == 80.0,
            f"tp={cov['tp_total']} cov={cov['tp_covered']} rate={cov['tp_rate']}",
        )
        check(
            "P6-②2-3 定位未覆盖缺口（1 FP + 1 TP）",
            cov["uncovered_fp_count"] == 1 and cov["uncovered_tp_count"] == 1,
            f"gapFP={cov['uncovered_fp_count']} gapTP={cov['uncovered_tp_count']}",
        )
        check(
            "P6-②2-4 未覆盖明细正确（fp_E / TP-5）",
            cov["uncovered_fps"][0]["contract_id"] == "fp_E"
            and cov["uncovered_tps"][0]["tp_id"] == "TP-5",
            f"fp={[f['contract_id'] for f in cov['uncovered_fps']]} "
            f"tp={[t['tp_id'] for t in cov['uncovered_tps']]}",
        )
        check(
            "P6-②2-5 模块级覆盖统计存在",
            bool(cov["module_coverage"]),
            f"modules={list(cov['module_coverage'])}",
        )
        r_cov = client.get(f"/api/projects/{pid}/coverage")
        check(
            "P6-②2-6 GET /coverage 返回 ok + fp_rate=80",
            r_cov.status_code == 200 and r_cov.json()["fp_rate"] == 80.0,
            f"status={r_cov.status_code}",
        )

        # ================= 合订 HTML 报告 =================
        html_text = analytics_module.render_trend_coverage_html(pid)
        check(
            "P6-②1/②2-7 HTML 含 趋势/Flaky/覆盖率 三区块",
            "执行趋势" in html_text
            and "Flaky" in html_text
            and "覆盖率" in html_text
            and "fp_E" in html_text,
            "HTML 三段齐全且含缺口定位",
        )
        r_tc = client.get(f"/api/projects/{pid}/reports/trend_coverage")
        check(
            "P6-②1/②2-8 GET /reports/trend_coverage 返回 HTML 文件",
            r_tc.status_code == 200 and "text/html" in r_tc.headers.get("content-type", ""),
            f"ct={r_tc.headers.get('content-type')}",
        )
    finally:
        cleanup(pid)


if __name__ == "__main__":
    print("=== 阶段6 批次2（P6-②1 趋势/flaky + P6-②2 覆盖率）自测 ===")
    test_b6_2()
    print("\n" + "=" * 60)
    print(f"结果：PASS {PASS} / FAIL {FAIL}")
    print("=" * 60)
    for line in LOG:
        if line.startswith("[FAIL]"):
            print(line)
    raise SystemExit(0 if FAIL == 0 else 1)
