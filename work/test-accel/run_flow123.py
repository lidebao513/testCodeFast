"""流程 1→3 串联 + 导出最终测试用例文档。

阶段1：目标仓库 git 可用校验 + 分析（产出功能点）
阶段2：导入测试点 JSON（263 条，含异常/安全/边界维度）
阶段3：测试点驱动生成用例 + 导出 TEST_CASES.md / test_cases.json
"""

import collections

import backend.main as m  # 仅取其 _analyze_project（注册在 startup 之前的纯函数）
from backend.db import get_conn, init_db
from backend.modules import tp_store
from backend.modules.case_generator import case_generator
from backend.modules.project_manager import pm


def main():
    init_db()
    proj = pm.find_by_name("research-agent")
    if not proj:
        raise SystemExit("research-agent 项目未注册，请先启动服务或手动注册")
    pid = proj["id"]
    print(f"[项目] {proj['name']} (id={pid})  local_path={proj['local_path']}")

    # 清理历史软删残留，避免文档计数膨胀
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM cases WHERE project_id=? AND status='archived'", (pid,))
    conn.commit()
    conn.close()

    # —— 阶段1 + 阶段2（功能点）：用综合构建器统一口径（C-★6）——
    fps, commit = m._analyze_project(pid)
    by_type = collections.Counter(f["ftype"] for f in fps)
    print(f"[阶段1/2 功能点] 总数={len(fps)}  按类型={dict(by_type)}  commit={commit[:8]}")

    # —— 阶段2（测试点）：导入离线生成的 263 条测试点 ——
    imp = tp_store.import_test_points(pid)
    print(
        f"[阶段2 测试点] 导入={imp['imported']} 文件={imp['tp_json']}  按类别={imp['by_category']}"
    )

    # —— 阶段3：测试点驱动生成用例 + 导出文档 ——
    n = case_generator.generate_for_project(pid)
    exp = case_generator.export_test_cases(pid)
    print(f"[阶段3 用例] 生成={n}  导出MD={exp['md_path']}  JSON={exp['json_path']}")

    # 汇总
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT case_type, priority, COUNT(*) c FROM cases "
        "WHERE project_id=? AND status<>'archived' GROUP BY case_type, priority",
        (pid,),
    )
    rows = cur.fetchall()
    by_cp = collections.Counter()
    by_pri = collections.Counter()
    for r in rows:
        by_cp[f"{r['case_type']}/{r['priority']}"] += r["c"]
        by_pri[r["priority"]] += r["c"]
    cur.execute(
        "SELECT COUNT(*) c FROM cases WHERE project_id=? AND status<>'archived' "
        "AND tp_id LIKE 'TP-%'",
        (pid,),
    )
    stable = cur.fetchone()["c"]
    cur.execute(
        "SELECT COUNT(*) c FROM cases c JOIN functional_points f "
        "ON c.fp_contract_id=f.contract_id WHERE c.project_id=? AND c.status<>'archived'",
        (pid,),
    )
    resolved = cur.fetchone()["c"]
    conn.close()

    print(
        f"[汇总] 用例总数={n}  稳定ID(TP-%)用例={stable}  "
        f"fp_contract_id行级可解析={resolved}/{n} "
        f"(孤儿={n - resolved})"
    )
    print(f"[汇总] 按 类型/优先级 = {dict(by_cp)}")
    print(f"[汇总] 按优先级 = {dict(by_pri)}")
    print("DONE")


if __name__ == "__main__":
    main()
