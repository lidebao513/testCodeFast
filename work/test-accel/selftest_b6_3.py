"""阶段6 批次3 自测（P6-②3 导出 + P6-④ 执行摘要）。

覆盖：
 1) reporter.build_exec_summary 返回结构化结论（headline/bullets/metrics/trend/...）
 2) exporters.export_report 产出 xlsx/docx/pdf 三格式（存在/非空/扩展名正确/PDF 以 %PDF 开头）
 3) 端点 GET /exec_summary、/reports/{rid}/summary、/reports/{rid}/export?fmt=
 4) 综合 HTML 报告含「执行摘要」卡片（重新生成一份验证渲染）
"""

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from backend.config import settings
from backend.db import get_conn
from backend.main import app
from backend.modules import exporters as exporters_module
from backend.modules import reporter as reporter_module


PID = 2  # research-agent
PASS, FAIL = 0, 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {extra}")


def pick_report_with_json():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, html_path FROM reports WHERE project_id=? ORDER BY id DESC", (PID,))
    for r in cur.fetchall():
        jp = Path(r["html_path"]).with_suffix(".json")
        if jp.exists():
            conn.close()
            return r["id"], jp
    conn.close()
    return None, None


print("===== 阶段6 批次3 自测 (P6-②3 + P6-④) =====")

rid, json_path = pick_report_with_json()
check("B3-0 选定带 JSON 的报告", rid is not None, f"rid={rid}")
if rid is None:
    print(f"\n结果：PASS {PASS} / FAIL {FAIL}")
    sys.exit(1)

# ---- 1) build_exec_summary ----
print("\n[1] reporter.build_exec_summary")
es = reporter_module.reporter.build_exec_summary(PID, rid)
check("B3-1 返回非 None", es is not None)
check("B3-2 含 headline", bool(es and es.get("headline")), str(es))
check("B3-3 含 bullets 列表", bool(es and isinstance(es.get("bullets"), list) and es["bullets"]))
check("B3-4 含 metrics", bool(es and isinstance(es.get("metrics"), dict)))
check(
    "B3-5 含 trend/fp_rate/tp_rate/flaky",
    bool(es and "trend" in es and "fp_rate" in es and "tp_rate" in es and "flaky" in es),
)
m = (es or {}).get("metrics", {})
print(f"     摘要：{es['headline']}")
print(
    f"     指标：{m}  趋势={es.get('trend')} FP={es.get('fp_rate')}% TP={es.get('tp_rate')}% flaky={es.get('flaky')}"
)

# ---- 2) exporters.export_report 三格式 ----
print("\n[2] exporters.export_report (xlsx/docx/pdf)")
out_dir = settings.REPORTS_DIR
xp = exporters_module.export_report(PID, rid, "xlsx", out_dir)
dp = exporters_module.export_report(PID, rid, "docx", out_dir)
pp = exporters_module.export_report(PID, rid, "pdf", out_dir)
check("B3-6 xlsx 文件存在", xp and Path(xp).exists(), str(xp))
check("B3-7 xlsx 非空(>500B)", xp and Path(xp).stat().st_size > 500)
check("B3-8 xlsx 扩展名", xp and Path(xp).suffix == ".xlsx")
check("B3-9 docx 文件存在", dp and Path(dp).exists())
check("B3-10 docx 非空(>500B)", dp and Path(dp).stat().st_size > 500)
check("B3-11 docx 扩展名", dp and Path(dp).suffix == ".docx")
check("B3-12 pdf 文件存在", pp and Path(pp).exists())
check("B3-13 pdf 非空(>500B)", pp and Path(pp).stat().st_size > 500)
check("B3-14 pdf 以 %PDF 开头", pp and Path(pp).read_bytes()[:5] == b"%PDF-")
check(
    "B3-15 别名容错(excel→xlsx)", bool(exporters_module.export_report(PID, rid, "excel", out_dir))
)
print(f"     产物：\n       {xp}\n       {dp}\n       {pp}")

# ---- 3) 端点（TestClient）----
print("\n[3] HTTP 端点")
with TestClient(app) as client:
    r1 = client.get(f"/api/projects/{PID}/exec_summary")
    check("B3-16 /exec_summary 200", r1.status_code == 200, r1.text[:120])
    check("B3-17 /exec_summary ok+headline", r1.json().get("ok") and r1.json().get("headline"))

    r2 = client.get(f"/api/projects/{PID}/reports/{rid}/summary")
    check("B3-18 /reports/{rid}/summary 200", r2.status_code == 200, r2.text[:120])
    check("B3-19 summary 含 headline", bool(r2.json().get("headline")))

    for fmt, sub in [("xlsx", "spreadsheetml"), ("docx", "wordprocessingml"), ("pdf", "pdf")]:
        rr = client.get(f"/api/projects/{PID}/reports/{rid}/export?fmt={fmt}")
        check(f"B3-20 export {fmt} 200", rr.status_code == 200, rr.text[:80])
        check(
            f"B3-21 export {fmt} content-type",
            sub in rr.headers.get("content-type", ""),
            rr.headers.get("content-type", ""),
        )
    # 未知 fmt 应回退不报错
    rr2 = client.get(f"/api/projects/{PID}/reports/{rid}/export?fmt=unknown")
    check("B3-22 未知 fmt 不崩(回落 xlsx)", rr2.status_code == 200)

# ---- 4) 综合 HTML 报告含执行摘要卡片 ----
print("\n[4] 综合 HTML 报告渲染执行摘要卡片")
results = json.loads(Path(json_path).read_text(encoding="utf-8")).get("results", [])
detail = reporter_module.reporter.build_report_detail(PID, rid, inline=False)
proj = detail.get("summary", {}).get("project", "research-agent") if detail else "research-agent"
new = reporter_module.reporter.build(
    PID, results, meta={"project": proj, "batch_id": "selftest_b6_3"}
)
new_html = Path(new["html_path"]).read_text(encoding="utf-8")
check("B3-23 新报告含「执行摘要」卡片", "执行摘要（一句话结论）" in new_html)
check(
    "B3-24 新报告含 headline 文案",
    bool(new.get("summary", {}).get("exec_summary", {}).get("headline")),
)
check("B3-25 新报告含趋势/覆盖率行", "趋势：" in new_html and "覆盖率：FP" in new_html)

print(f"\n===== 结果：PASS {PASS} / FAIL {FAIL} =====")
sys.exit(1 if FAIL else 0)
