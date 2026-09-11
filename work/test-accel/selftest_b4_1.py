"""阶段4 批次1 自测：D-★4（异常防护 / 异常不丢结果）+ D-★5（batch_id 贯穿 runs/reports）。

验证项：
 B4-1  每轮执行生成唯一 batch_id，本轮所有 result 与 runs 记录 batch 一致
 B4-2  正常轮次：results 数 == runs 落库数 == 用例数（评审门 blocked_review）
 B4-3  单条异常隔离：注入非法 steps JSON → 仅该条 error，整轮未中断（仍 263 条）
 B4-4  异常不丢结果：发生 error 的轮次，runs 落库数仍 == 263
 B4-5  未捕获异常保底：中途抛 BaseException（绕过单条 try）→ 已执行部分仍落库
 B4-6  回归：修复异常数据后执行，error == 0，结果与改动前口径一致
 B4-7  报告关联：reports.batch_id == 本轮 runs.batch_id（可按批次回溯）
 B4-8  端点可用：/runs?batch_id= 精确回溯；/batches 返回多轮分布
"""

import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import backend.db as db
from backend.config import PROJECT_ROOT, settings
from backend.main import _analyze_project, app, bulk_review
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.executor import executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


class Boom(BaseException):
    """非 Exception 子类：用于验证 finally 保底（内部 except Exception 不会捕获）。"""


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

    # 干净基线
    conn = db.get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    cur.close()

    _analyze_project(pid)
    tp_store.import_test_points(pid)
    n = case_generator.generate_for_project(pid)
    assert n == 263, f"expected 263 cases, got {n}"
    print(f"[setup] 项目 {pid}：用例 {n} 条（REVIEW_GATE={settings.REVIEW_GATE}）")

    # ---------- 轮1：评审门（未审核） ----------
    r1 = executor.run_project(pid)
    bid1 = executor.last_batch_id
    blocked = sum(1 for r in r1 if r["status"] == "blocked_review")
    check(
        "B4-1 本轮所有 result 携带一致且非空的 batch_id",
        bool(bid1) and all(r.get("batch_id") == bid1 for r in r1),
        f"batch={bid1}",
    )
    check(
        "B4-2 评审门轮次：results/runs 数 == 263 且全为 blocked_review",
        len(r1) == 263 and blocked == 263,
        f"results={len(r1)}, blocked={blocked}",
    )

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid1))
    runs1 = cur.fetchone()["c"]
    check("B4-2b runs 落库数 == 263 且均带 batch_id", runs1 == 263, f"runs={runs1}")
    conn.close()

    # ---------- 轮2：注入单条非法 steps（验证异常隔离） ----------
    bulk_review(pid, type("R", (), {"action": "approve", "comment": "b4", "ids": None})())
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, steps FROM cases WHERE project_id=? AND status!='archived' ORDER BY id LIMIT 1",
        (pid,),
    )
    row = cur.fetchone()
    victim_id, victim_steps = row["id"], row["steps"]
    cur.execute("UPDATE cases SET steps='{NOT_VALID_JSON' WHERE id=?", (victim_id,))
    conn.commit()
    conn.close()

    r2 = executor.run_project(pid)
    bid2 = executor.last_batch_id
    errs = [r for r in r2 if r["status"] == "error"]
    check(
        "B4-3 单条异常隔离：仅该条 error，整轮未中断（仍 263 条结果）",
        len(r2) == 263 and len(errs) == 1 and errs[0]["case_id"] == victim_id,
        f"results={len(r2)}, error={len(errs)}",
    )
    check(
        "B4-3b error 结果带可诊断的异常原因",
        bool(errs) and "executor_error" in (errs[0].get("reason") or ""),
        (errs[0].get("reason") or "")[:80] if errs else "",
    )

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid2))
    runs2 = cur.fetchone()["c"]
    check("B4-4 异常不丢结果：发生 error 的轮次 runs 仍落库 263 条", runs2 == 263, f"runs={runs2}")
    conn.close()

    # ---------- 轮3：未捕获异常保底（finally commit） ----------
    orig_run_case = executor._run_case
    state = {"n": 0}
    TRIGGER = 100

    def boom_at_100(c, proj, service_up, ctx=None):
        state["n"] += 1
        if state["n"] == TRIGGER:
            raise Boom("simulated fatal at case #100")
        return orig_run_case(c, proj, service_up, ctx)

    executor._run_case = boom_at_100
    raised = False
    try:
        # 显式串行：并发路径按 50 条一批「先执行后写库」，崩溃时只丢当前批次；
        # 串行路径逐条写库 + finally 补提交，才是"已执行部分全部保住"的语义。
        executor.run_project(pid, max_workers=1)
    except Boom:
        raised = True
    finally:
        executor._run_case = orig_run_case
    bid3 = executor.last_batch_id

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid3))
    runs3 = cur.fetchone()["c"]
    conn.close()
    check(
        "B4-5 未捕获异常保底：中途崩溃时已执行部分仍落库（99 条未丢失）",
        raised and runs3 == TRIGGER - 1,
        f"raised={raised}, persisted={runs3}（期望 {TRIGGER - 1}）",
    )

    # ---------- 轮4：修复数据后回归 ----------
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE cases SET steps=? WHERE id=?", (victim_steps, victim_id))
    conn.commit()
    conn.close()
    bulk_review(pid, type("R", (), {"action": "approve", "comment": "b4", "ids": None})())

    r4 = executor.run_project(pid)
    bid4 = executor.last_batch_id
    errs4 = [r for r in r4 if r["status"] == "error"]
    skipped4 = [r for r in r4 if r["status"] == "skipped"]
    blocked4 = [r for r in r4 if r["status"] == "blocked_review"]
    check(
        "B4-6 回归：修复后 error==0 / blocked==0 / skipped==0（与改动前口径一致）",
        len(r4) == 263 and not errs4 and not skipped4 and not blocked4,
        f"results={len(r4)}, error={len(errs4)}, skipped={len(skipped4)}, blocked={len(blocked4)}",
    )
    check(
        "B4-6b 多轮 batch_id 互不相同（可区分轮次）",
        len({bid1, bid2, bid3, bid4}) == 4,
        f"{[bid1, bid2, bid3, bid4]}",
    )

    # ---------- 轮4：报告关联 ----------
    rep = reporter.build(pid, r4, meta={"project": "research-agent", "batch_id": bid4})
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT batch_id FROM reports WHERE id=?", (rep["id"],))
    rep_batch = cur.fetchone()["batch_id"]
    cur.execute("SELECT COUNT(*) c FROM runs WHERE project_id=? AND batch_id=?", (pid, bid4))
    runs4 = cur.fetchone()["c"]
    conn.close()
    check(
        "B4-7 报告关联：reports.batch_id == 本轮 runs.batch_id",
        rep_batch == bid4 and runs4 == 263,
        f"report_batch={rep_batch}, runs={runs4}",
    )

    # ---------- 端点验证 ----------
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(f"/api/projects/{pid}/runs", params={"batch_id": bid4})
    ok_runs = resp.status_code == 200 and len(resp.json()) == 263
    check(
        "B4-8 /runs?batch_id= 可按批次精确回溯 263 条",
        ok_runs,
        f"http={resp.status_code}, n={len(resp.json()) if resp.status_code == 200 else '-'}",
    )

    resp2 = client.get(f"/api/projects/{pid}/batches")
    batches = resp2.json() if resp2.status_code == 200 else []
    bmap = {b["batch_id"]: b for b in batches}
    ok_b = resp2.status_code == 200 and len(batches) >= 4 and bmap.get(bid4, {}).get("total") == 263
    check(
        "B4-8b /batches 返回多轮批次分布（含本轮 263 条）",
        ok_b,
        f"batches={len(batches)}, 本轮={bmap.get(bid4, {})}",
    )
    if bmap.get(bid2):
        check(
            "B4-8c 批次概览正确统计 error 轮次（error=1）",
            bmap[bid2]["errored"] == 1,
            f"轮2 分布={bmap[bid2]}",
        )

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    cost = int(time.time() - t0)
    print(f"\n==== 批次1 自测汇总：{passed}/{total} 通过，耗时 {cost}s ====")
    for name, ok, detail in _results:
        if not ok:
            print(f"  X {name} — {detail}")
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
