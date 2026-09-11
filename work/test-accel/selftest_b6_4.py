"""阶段6 批次4 自测：P6-②5 章节化全功能验证报告落地（6.1~6.4）。"""

import re
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name} {detail}")


from backend.db import get_conn
from backend.modules import full_report as fr


conn = get_conn()
PID = conn.execute("SELECT id FROM projects WHERE name='research-agent'").fetchone()[0]
conn.close()
print(f"project research-agent id={PID}\n")

print("== 6.1 数据聚合 ==")
d = fr.aggregate(PID)
check(
    "聚合返回 9 类关键字段",
    all(
        k in d
        for k in (
            "cases",
            "tps",
            "change",
            "batch",
            "runs",
            "by_module",
            "by_type",
            "monitor",
            "lifecycle",
        )
    ),
)
check(
    "用例清册非空且排除 obsolete",
    len(d["cases"]) > 0 and all(c["status"] not in ("obsolete", "archived") for c in d["cases"]),
)
check("测试点含模块/维度", all(t["module"] and t["dimension"] for t in d["tps"]))
check("监控时间线非空", len(d["monitor"]) > 0)
check("批次自动选取最近一次", d["batch"] is not None and d["batch"]["batch_id"])

print("\n== 6.2 模板渲染（HTML）==")
html = fr.render_html(d)
check("HTML 无未替换 token", "{{" not in html, "残留 {{token}}")
check(
    "9 章节齐全",
    all(
        s in html
        for s in [
            "一、变更摘要",
            "二、测试点设计",
            "三、完整测试用例清单",
            "四、用例明细与执行结果",
            "五、通过 / 失败统计",
            "六、结论与风险",
            "七、监控记录",
            "八、执行过程截图",
            "九、最终复用占比",
        ]
    ),
)
check("章节可折叠结构（sec-block + toggle）", html.count("sec-toggle") >= 9)
check("侧边目录容器", 'id="toc"' in html)
check("筛选条容器（测试点/用例/明细/监控）", html.count('class="filterbar"') >= 4)
check("KPI 卡渲染用例总数", str(len(d["cases"])) in html)

print("\n== 6.3 章节化 MD ==")
md = fr.render_md(d)
check("MD 9 个二级章节", len(re.findall(r"^## ", md, re.M)) == 9)
check("MD 用例清册行数 ≈ 用例数", md.count("\n|") >= len(d["cases"]))
check("MD 变更摘要含 commit 对", d["change"] is None or d["change"]["commit_from"] in md)

print("\n== 6.4 最终交付（generate 落盘 + 截图内嵌）==")
res = fr.generate(PID)
md_p, html_p = Path(res["md_path"]), Path(res["html_path"])
check("VERIFICATION_REPORT.md 生成", md_p.exists() and md_p.stat().st_size > 1000)
check("VERIFICATION_REPORT.html 生成", html_p.exists() and html_p.stat().st_size > 5000)
html2 = html_p.read_text(encoding="utf-8")
check("汇总数字一致", res["cases"] == len(d["cases"]) and res["test_points"] == len(d["tps"]))
if d["shots"]:
    check("截图 base64 内嵌", "data:image/png;base64," in html2)
else:
    check("无截图时给出说明文案", "暂无截图" in html2)

print("\n== 端点（FastAPI TestClient）==")
from fastapi.testclient import TestClient

from backend.main import app


with TestClient(app) as client:
    r = client.get(f"/api/projects/{PID}/reports/full?fmt=json")
    check("GET /reports/full fmt=json", r.status_code == 200 and r.json().get("ok"))
    r = client.get(f"/api/projects/{PID}/reports/full?fmt=md")
    check("GET /reports/full fmt=md", r.status_code == 200 and "## " in r.text)
    r = client.get(f"/api/projects/{PID}/reports/full")
    check(
        "GET /reports/full 默认 html",
        r.status_code == 200 and "text/html" in r.headers.get("content-type", ""),
    )
    # 静态路由不被 /reports/{rid} 拦截
    r = client.get(f"/api/projects/{PID}/reports/{999999}")
    check("/reports/{rid} 404 优雅", r.status_code == 200 and r.json().get("ok") is False)

print(f"\n===== {PASS} PASSED / {FAIL} FAILED =====")
sys.exit(1 if FAIL else 0)
