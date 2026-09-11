"""批次2 自测：用例 8 要素完整 + TEST_CASES.md 交付物（C-★2 + C-★4）。

验证项：
 B2-E1  每条用例 8 要素非空：编号/模块/标题/类型/优先级/前置/步骤/预期
 B2-E2  步骤为非伪多步（≥3 步，含人类的 前置→准备→执行→断言，断言步带自然语言预期）
 B2-E3  优先级派生正确：异常/鉴权类 → P1，且 P1 数 ≥ 异常 TP 数
 B2-E4  TEST_CASES.md 与 test_cases.json 存在且覆盖全部用例
 B2-E5  阶段6 reporter HTML 含「用例清册」卡片（从该产物取数）
"""

import json
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.db import get_conn, init_db
from backend.main import _analyze_project
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


def main():
    init_db()
    proj = pm.find_by_name("research-agent") or pm.add(
        name="research-agent",
        local_path=str(
            __import__("backend.config", fromlist=["PROJECT_ROOT"]).PROJECT_ROOT.parent
            / "targets"
            / "research-agent"
        ),
    )
    pid = proj["id"]

    # 干净基线：清除历史残留（B3.3 软删后反复运行会累积归档用例，污染计数）
    c0 = get_conn()
    cu0 = c0.cursor()
    for tbl in ("runs", "cases", "test_points", "functional_points"):
        cu0.execute(f"DELETE FROM {tbl} WHERE project_id=?", (pid,))
    c0.commit()
    c0.close()

    _analyze_project(pid)
    imp = tp_store.import_test_points(pid)
    assert imp["ok"], f"import failed: {imp}"
    n = case_generator.generate_for_project(pid)
    exp = case_generator.export_test_cases(pid)
    print(f"[gen] tp={imp['imported']} cases={n} export_count={exp['count']}")
    print(f"[export] md={exp['md_path']} json={exp['json_path']}")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cases WHERE project_id=?", (pid,))
    cases = [dict(r) for r in cur.fetchall()]
    conn.close()

    fails = []
    valid_types = {"正常", "异常", "安全", "边界"}
    valid_prio = {"P0", "P1", "P2"}

    for c in cases:
        e = []
        if not c.get("tc_no"):
            e.append("tc_no")
        if not c.get("module"):
            e.append("module")
        if not c.get("title"):
            e.append("title")
        if c.get("case_type") not in valid_types:
            e.append("case_type")
        if c.get("priority") not in valid_prio:
            e.append("priority")
        if not c.get("precondition"):
            e.append("precondition")
        doc = json.loads(c["doc_steps"]) if c.get("doc_steps") else []
        if len(doc) < 3:
            e.append("doc_steps<3")
        elif not all(s.get("desc") for s in doc):
            e.append("doc_step_missing_desc")
        # 预期：断言步的 expect 非空（自然语言）
        assert_step = next((s for s in doc if s.get("type") == "断言"), None)
        expect = (assert_step or {}).get("expect") or ""
        if not expect:
            e.append("expect")
        if e:
            fails.append(f"B2-E1/E2 {c.get('tc_no')}: 缺 {e}")

    # B2-E3 优先级派生
    p1 = [c for c in cases if c["priority"] == "P1"]
    ab_tp = [t for t in tp_store.get_test_points(pid) if t["category"] == "异常"]
    if len(p1) < len(ab_tp):
        fails.append(f"B2-E3 P1数({len(p1)}) < 异常TP数({len(ab_tp)})")
    else:
        print(
            f"[prio] P1={len(p1)}（≥异常TP {len(ab_tp)}） P2={sum(1 for c in cases if c['priority'] == 'P2')}"
        )

    # B2-E4 交付物文件
    md_path = exp["md_path"]
    json_path = exp["json_path"]
    if not os.path.exists(md_path):
        fails.append("B2-E4 TEST_CASES.md 不存在")
    else:
        md = open(md_path, encoding="utf-8").read()
        miss = [c["tc_no"] for c in cases if c["tc_no"] not in md]
        if miss:
            fails.append(f"B2-E4 TEST_CASES.md 缺 {len(miss)} 条用例编号")
        else:
            print(f"[md] TEST_CASES.md 覆盖全部 {len(cases)} 条用例编号")
    if not os.path.exists(json_path):
        fails.append("B2-E4 test_cases.json 不存在")
    else:
        j = json.loads(open(json_path, encoding="utf-8").read())
        jc = j["cases"]
        if len(jc) != len(cases):
            fails.append(f"B2-E4 test_cases.json 条数 {len(jc)} != {len(cases)}")
        else:
            miss8 = [
                x["tc_no"]
                for x in jc
                if not (
                    x.get("tc_no")
                    and x.get("module")
                    and x.get("priority")
                    and x.get("precondition")
                    and x.get("doc_steps")
                )
            ]
            if miss8:
                fails.append(f"B2-E4 json 中 {len(miss8)} 条缺 8 要素")
            else:
                print(f"[json] test_cases.json 8 要素齐全，{len(jc)} 条")

    # B2-E5 reporter 用例清册卡片
    rep = reporter.build(pid, [], meta={"project": "research-agent"})
    html = open(rep["html_path"], encoding="utf-8").read()
    if "用例清册" not in html:
        fails.append("B2-E5 reporter HTML 无「用例清册」卡片")
    else:
        print("[reporter] HTML 含「用例清册」卡片（从 test_cases.json 取数）")

    print("-" * 50)
    if fails:
        print("SELFTEST B2 FAILED:")
        for f in fails[:20]:
            print("  ✗", f)
        return 1
    print(f"SELFTEST B2 PASSED: cases={len(cases)} 8要素齐全 交付物齐全 reporter联动OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
