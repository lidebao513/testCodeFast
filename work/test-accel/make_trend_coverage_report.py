"""生成「趋势 + flaky + 覆盖率」合订 HTML 报告（阶段6 批次2）。

动作：取 research-agent 项目 → 调用 analytics 分析现有执行历史 → 产出
      data/reports/trend_coverage_{pid}_{ts}.html（可直接打开）。
只读分析，不改写任何数据。
说明：趋势的"真实通过率"取决于是否开启动态探测（ENABLE_DYNAMIC_PROBE=on
且被测服务在线）；演示环境未开时 pass_rate 多为 None，趋势将呈现"执行规模"
与"仅静态验证"维度，仍为有效诊断信息。
"""

import time

from backend.config import settings
from backend.db import init_db
from backend.modules import analytics as analytics_module
from backend.modules.project_manager import pm


def main():
    init_db()
    proj = pm.find_by_name("research-agent")
    if not proj:
        print("research-agent 项目不存在，请先 run_full_flow.py 建库")
        return None
    pid = proj["id"]

    tr = analytics_module.trend(pid)
    fl = analytics_module.flaky(pid)
    cov = analytics_module.coverage(pid)
    print(
        f"[analytics] 批次={tr['count']} 方向={tr['pass_rate_direction']} "
        f"flaky={fl['flaky_count']} FP覆盖={cov['fp_rate']}% TP覆盖={cov['tp_rate']}%"
    )

    html = analytics_module.render_trend_coverage_html(pid)
    out_dir = settings.REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"trend_coverage_{pid}_{ts}.html"
    path.write_text(html, encoding="utf-8")
    print(f"[report] 已写出 {path}")
    return str(path)


if __name__ == "__main__":
    main()
