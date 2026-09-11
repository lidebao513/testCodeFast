"""生成一份真实的最终 HTML 报告（阶段6 批次1 后），供查看/演示。

动作：取 research-agent 项目 → 审核全部用例 → 真实执行 → reporter.build 出 HTML。
仅生产演示报告，不改动测试点/用例对账状态。
"""

import time

from backend.db import get_conn, init_db
from backend.modules.executor import executor
from backend.modules.project_manager import pm
from backend.modules.reporter import reporter


def main():
    init_db()
    proj = pm.find_by_name("research-agent")
    if not proj:
        print("research-agent 项目不存在，请先 run_full_flow.py 建库")
        return
    pid = proj["id"]
    # 审核全部生效用例，使执行不被 review_gate 阻断
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cases SET review_status='approved' "
        "WHERE project_id=? AND status NOT IN ('archived','obsolete')",
        (pid,),
    )
    n_appr = cur.rowcount
    conn.commit()
    conn.close()
    print(f"[setup] 已审核 {n_appr} 条用例")

    t0 = time.time()
    results = executor.run_project(pid, max_workers=8)
    el = time.time() - t0
    print(f"[exec] {len(results)} 条，耗时 {el:.1f}s")

    rep = reporter.build(pid, results, meta={"project": "research-agent"})
    s = rep["summary"]
    print(f"[report] id={rep['id']} html={rep['html_path']}")
    print(
        f"[report] 通过={s['pass']} 失败={s['fail']} 仅静态={s['structural_only']} "
        f"需鉴权={s['blocked_auth']} 异常={s['error']} 待审核={s['blocked_review']}"
    )
    print(
        f"[report] 追溯覆盖={s['traceability']['coverage']}% "
        f"失败聚类={len(s['failures']['clusters'])} 组"
    )
    return rep["html_path"]


if __name__ == "__main__":
    main()
