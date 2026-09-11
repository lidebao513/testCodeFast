"""阶段1→阶段3 端到端串联自测（B3.6）。

完整跑通：阶段1(取码/分析) → 阶段2(测试点) → 阶段3(导入/生成/审核/执行/报告)，
验证各阶段衔接与整体正确性，覆盖核心流程、边界与异常处理。

不启动 uvicorn，直接调用平台内部模块；通过切换设置态验证评审门闭环。
"""

import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import backend.db as db
from backend.config import PROJECT_ROOT
from backend.main import _analyze_project
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.code_analyzer import _git_repo_usable
from backend.modules.executor import executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


TARGET = PROJECT_ROOT.parent / "targets" / "research-agent"
TP_JSON = PROJECT_ROOT.parent / "research-agent-test" / "test_points_new.json"
PULL_RESULT = PROJECT_ROOT.parent / "targets" / ".pull_result.json"

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))


def q_one(cur, sql, params=()):
    cur.execute(sql, params)
    r = cur.fetchone()
    return r[0] if r else None


def main():
    t0 = time.time()
    db.init_db()
    # 确保 research-agent 项目已注册（仅本地路径依赖）
    if not pm.find_by_name("research-agent"):
        pm.add(
            name="research-agent",
            local_path=str(TARGET),
            type="pc",
            base_url="http://localhost:8010",
        )
    proj = pm.find_by_name("research-agent")
    pid = proj["id"]

    # 干净基线：清除历史残留（此前 selftest_b1/b2 的归档用例会污染计数），
    # 阶段3 全部由此轮重新生成，保证端到端结果可独立判定。
    conn = db.get_conn()
    cur = conn.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cur.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    conn.commit()
    cur.close()
    conn = db.get_conn()
    cur = conn.cursor()

    # ============ 阶段1：取码 / 分析 ============
    print("\n=== 阶段1：取码 / 分析 ===")
    check("E2E-S1a 目标仓库为独立 git 仓库（防父仓库误伤）", _git_repo_usable(str(TARGET)))
    check("E2E-S1b 阶段1 产物 .pull_result.json 存在", PULL_RESULT.exists())
    if PULL_RESULT.exists():
        pr = json.loads(PULL_RESULT.read_text(encoding="utf-8"))
        check(
            "E2E-S1c .pull_result 含 changed_count 字段",
            "changed_count" in pr,
            f"changed_count={pr.get('changed_count')}",
        )

    # analyze：C-★6 修复后用综合构建器（含 business 维度）
    fps, _ = _analyze_project(pid)
    cur.execute(
        "SELECT ftype, COUNT(*) c FROM functional_points WHERE project_id=? GROUP BY ftype", (pid,)
    )
    by_type = {r["ftype"]: r["c"] for r in cur.fetchall()}
    check(
        "E2E-S1d analyze 产出功能点（>200，覆盖 api/page/component/business）",
        sum(by_type.values()) > 200,
        f"by_type={by_type}",
    )
    check(
        "E2E-S1e analyze 含 business 维度（C-★6 修复标志）",
        by_type.get("business", 0) > 0,
        f"business={by_type.get('business', 0)}",
    )
    # 统一契约字段落地
    cur.execute(
        "SELECT COUNT(*) c FROM functional_points "
        "WHERE project_id=? AND contract_id IS NOT NULL "
        "AND title IS NOT NULL AND module IS NOT NULL",
        (pid,),
    )
    check(
        "E2E-S1f 功能点统一契约字段(contract_id/title/module)完整",
        q_one(cur, "SELECT COUNT(*) c FROM functional_points WHERE project_id=?", (pid,)) > 0
        and q_one(
            cur,
            "SELECT COUNT(*) c FROM functional_points WHERE project_id=? "
            "AND contract_id IS NOT NULL AND title IS NOT NULL "
            "AND module IS NOT NULL",
            (pid,),
        )
        == sum(by_type.values()),
    )

    # ============ 阶段2：测试点 ============
    print("\n=== 阶段2：测试点 ===")
    check("E2E-S2a test_points_new.json 存在", TP_JSON.exists())
    tp_data = json.loads(TP_JSON.read_text(encoding="utf-8"))
    tps = tp_data["test_points"]
    check("E2E-S2b 测试点数 == 263（与已知基线一致）", len(tps) == 263, f"n={len(tps)}")
    cats = {}
    for t in tps:
        cats[t.get("tp_type")] = cats.get(t.get("tp_type"), 0) + 1
    check("E2E-S2c 含异常维度（26 条）", cats.get("异常", 0) == 26, f"by_type={cats}")
    check(
        "E2E-S2d 每条 TP 带稳定 tp_id(TP-xxx) 与 fp_id(FP-xxxx)",
        all(
            t.get("id", "").startswith("TP-") and t.get("fp_id", "").startswith("FP-") for t in tps
        ),
    )

    # ============ 阶段3：导入 → 生成 → 审核 → 执行 → 报告 ============
    print("\n=== 阶段3：导入 / 生成 / 审核 / 执行 / 报告 ===")

    # 导入测试点
    imp = tp_store.import_test_points(pid)
    check(
        "E2E-S3a 导入测试点 == 263",
        imp.get("ok") and imp.get("imported") == 263,
        str(imp.get("by_category")),
    )

    # 生成用例（REVIEW_GATE 默认 on → 全部 pending）
    n = case_generator.generate_for_project(pid)
    check("E2E-S3b 生成用例 == 263（TP→Case 1:1）", n == 263, f"n={n}")
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND tp_id IS NOT NULL", (pid,))
    check(
        "E2E-S3c 零孤儿：每条用例均带非空 tp_id",
        q_one(cur, "SELECT COUNT(*) c FROM cases WHERE project_id=? AND tp_id IS NULL", (pid,))
        == 0,
    )

    # C-★6 验证：fp_contract_id 行级可解析
    cur.execute("SELECT contract_id FROM functional_points WHERE project_id=?", (pid,))
    fp_contract_set = {r[0] for r in cur.fetchall() if r[0]}
    cur.execute("SELECT fp_contract_id FROM cases WHERE project_id=?", (pid,))
    total_case = 0
    unresolved = 0
    for (fc,) in cur.fetchall():
        total_case += 1
        if fc not in fp_contract_set:
            unresolved += 1
    check(
        "E2E-S3d C-★6：全部用例的 fp_contract_id 在 functional_points 行级可解析",
        unresolved == 0,
        f"unresolved={unresolved}/{total_case}",
    )

    # 8 要素非空
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=?", (pid,))
    total_cases = q_one(cur, "SELECT COUNT(*) c FROM cases WHERE project_id=?", (pid,))
    cur.execute(
        """SELECT COUNT(*) c FROM cases WHERE project_id=?
           AND module IS NOT NULL AND module<>''
           AND case_type IS NOT NULL AND priority IS NOT NULL
           AND precondition IS NOT NULL AND doc_steps IS NOT NULL
           AND tc_no IS NOT NULL""",
        (pid,),
    )
    eight_ok = q_one(
        cur,
        """SELECT COUNT(*) c FROM cases WHERE project_id=?
           AND module IS NOT NULL AND module<>''
           AND case_type IS NOT NULL AND priority IS NOT NULL
           AND precondition IS NOT NULL AND doc_steps IS NOT NULL
           AND tc_no IS NOT NULL""",
        (pid,),
    )
    check(
        "E2E-S3e 8 要素（编号/模块/类型/优先级/前置/步骤）非空",
        total_cases == eight_ok and total_cases == 263,
        f"non-empty={eight_ok}/{total_cases}",
    )

    # 异常维度进入用例
    cur.execute(
        "SELECT COUNT(*) c FROM cases WHERE project_id=? AND case_type='异常' "
        "AND status!='archived'",
        (pid,),
    )
    check(
        "E2E-S3f 异常维度进入用例（== 26）",
        q_one(
            cur,
            "SELECT COUNT(*) c FROM cases WHERE project_id=? AND case_type='异常' "
            "AND status!='archived'",
            (pid,),
        )
        == 26,
    )

    # 稳定 ID 形态
    cur.execute(
        "SELECT COUNT(*) c FROM cases WHERE project_id=? AND tp_id LIKE 'TP-%' "
        "AND status!='archived'",
        (pid,),
    )
    check(
        "E2E-S3g 用例稳定 ID 形如 TP-xxx",
        q_one(
            cur,
            "SELECT COUNT(*) c FROM cases WHERE project_id=? AND tp_id LIKE 'TP-%' "
            "AND status!='archived'",
            (pid,),
        )
        == 263,
    )

    # 软删版本：第1轮
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND status!='archived'", (pid,))
    active1 = q_one(
        cur, "SELECT COUNT(*) c FROM cases WHERE project_id=? AND status!='archived'", (pid,)
    )
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND status='archived'", (pid,))
    arch1 = q_one(
        cur, "SELECT COUNT(*) c FROM cases WHERE project_id=? AND status='archived'", (pid,)
    )
    check(
        "E2E-S3h(1) 首轮生成：生效263 / 归档0",
        active1 == 263 and arch1 == 0,
        f"active={active1}, archived={arch1}",
    )

    # 评审门（REVIEW_GATE 默认 on）：未审核 → 全部 blocked_review
    res1 = executor.run_project(pid)
    blocked1 = sum(1 for r in res1 if r.get("status") == "blocked_review")
    check(
        "E2E-S3i(1) 评审门：未审核用例全部 blocked_review（==263）",
        blocked1 == 263,
        f"blocked={blocked1}",
    )

    # 批量审核放行
    from backend.main import bulk_review

    br = bulk_review(
        pid, type("R", (), {"action": "approve", "comment": "e2e auto", "ids": None})()
    )
    check(
        "E2E-S3i(2) 批量审核更新 263 条为 approved",
        br.get("updated") == 263 and br.get("review_status") == "approved",
        str(br),
    )

    # 审核后执行：不再 blocked；非 API 用例也真实执行（非 skipped）
    res2 = executor.run_project(pid)
    blocked2 = sum(1 for r in res2 if r.get("status") == "blocked_review")
    skipped = sum(1 for r in res2 if r.get("status") == "skipped")
    check("E2E-S3i(3) 审核放行后 blocked_review == 0", blocked2 == 0, f"blocked={blocked2}")
    check(
        "E2E-S3i(4) 执行结果无 skipped（含 page/component/business 均被派发执行）",
        skipped == 0,
        f"skipped={skipped}",
    )
    # 非 API 用例（ctype=e2e）不应被 skipped
    cur.execute(
        "SELECT COUNT(*) c FROM cases WHERE project_id=? AND ctype='e2e' AND status='skipped'",
        (pid,),
    )
    check(
        "E2E-S3i(5) 前端/业务类(e2e)用例未 skipped",
        q_one(
            cur,
            "SELECT COUNT(*) c FROM cases WHERE project_id=? AND ctype='e2e' AND status='skipped'",
            (pid,),
        )
        == 0,
    )

    # 软删版本：第2轮（重新生成，旧轮归档）
    n2 = case_generator.generate_for_project(pid)
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND status!='archived'", (pid,))
    active2 = q_one(
        cur, "SELECT COUNT(*) c FROM cases WHERE project_id=? AND status!='archived'", (pid,)
    )
    cur.execute("SELECT COUNT(*) c FROM cases WHERE project_id=? AND status='archived'", (pid,))
    arch2 = q_one(
        cur, "SELECT COUNT(*) c FROM cases WHERE project_id=? AND status='archived'", (pid,)
    )
    check(
        "E2E-S3h(2) 二次生成：生效263（新）/ 归档≥263（旧轮保留，历史 runs 不悬挂）",
        active2 == 263 and arch2 >= 263,
        f"active={active2}, archived={arch2}",
    )

    # 重新审核放行后执行 + 报告 + 交付物
    bulk_review(pid, type("R", (), {"action": "approve", "comment": "e2e auto", "ids": None})())
    res3 = executor.run_project(pid)
    # 报告：含用例清册卡片
    rep = reporter.build(pid, res3, meta={"project": proj["name"]})
    html_path = Path(rep["html_path"])
    check(
        "E2E-S3j 报告 HTML 生成且含『用例清册』卡片",
        html_path.exists() and "用例清册" in html_path.read_text(encoding="utf-8"),
        str(html_path),
    )

    # 交付物
    exp = case_generator.export_test_cases(pid)
    md = Path(exp["md_path"])
    js = Path(exp["json_path"])
    check(
        "E2E-S3k TEST_CASES.md 交付物存在且含 263 条用例",
        md.exists() and "263" in md.read_text(encoding="utf-8", errors="ignore"),
        str(md),
    )
    check(
        "E2E-S3l test_cases.json 交付物存在且 cases 数==263",
        js.exists() and json.loads(js.read_text(encoding="utf-8"))["summary"]["count"] == 263,
    )

    # 全量/新增 类型字段（C：全量/新增 类型字段）
    cur.execute("SELECT DISTINCT test_type FROM cases WHERE project_id=?", (pid,))
    ttypes = {r["test_type"] for r in cur.fetchall()}
    check(
        "E2E-S3l2 全量扫描用例 test_type 全部为『全量』", ttypes == {"全量"}, f"test_type={ttypes}"
    )
    js_data = json.loads(js.read_text(encoding="utf-8"))
    check(
        "E2E-S3l3 交付物 summary 含 by_test_type 且 全量=263",
        "by_test_type" in js_data["summary"]
        and js_data["summary"]["by_test_type"].get("全量") == 263,
        str(js_data["summary"].get("by_test_type")),
    )

    # 增量（新增）路径：generate_for_fp_ids 应赋值 test_type=『新增』
    cur.execute("SELECT id FROM functional_points WHERE project_id=? LIMIT 1", (pid,))
    fid = cur.fetchone()["id"]
    inc = case_generator.generate_for_fp_ids(pid, [fid])
    cur.execute("SELECT test_type FROM cases WHERE id=?", (inc["case_ids"][0],))
    inc_tt = cur.fetchone()["test_type"]
    check(
        "E2E-S3l4 增量生成(generate_for_fp_ids)用例 test_type=『新增』",
        inc.get("created", 0) >= 1 and inc_tt == "新增",
        f"created={inc.get('created')}, test_type={inc_tt}",
    )

    # 异常分支：审核 reject 后不应放行（用一条用例验证）
    # 取一条非归档用例 reject 之，run 后该条应为 blocked_review
    cur.execute("SELECT id FROM cases WHERE project_id=? AND status!='archived' LIMIT 1", (pid,))
    one_id = cur.fetchone()["id"]
    from backend.main import ReviewReq, review_case

    review_case(pid, one_id, ReviewReq(action="reject", comment="e2e negative"))
    res4 = executor.run_project(pid)
    one_res = [r for r in res4 if r.get("case_id") == one_id]
    check(
        "E2E-S3m 异常分支：reject 后该用例仍 blocked_review（评审门有效）",
        bool(one_res) and one_res[0].get("status") == "blocked_review",
        str(one_res[0] if one_res else None),
    )

    conn.close()

    # ============ 汇总 ============
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    cost = int(time.time() - t0)
    print(f"\n==== 端到端自测汇总：{passed}/{total} 通过，耗时 {cost}s ====")
    for name, ok, detail in _results:
        if not ok:
            print(f"  ❌ {name} — {detail}")
    return passed == total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
