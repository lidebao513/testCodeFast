import sys
from collections import defaultdict
sys.path.insert(0, ".")
from backend.db import get_conn

c = get_conn()
rows = list(c.execute(
    "SELECT name,ftype,file_path FROM functional_points WHERE project_id=2 ORDER BY ftype,id"
))
g = defaultdict(list)
for r in rows:
    g[r["ftype"]].append(r)

lines = []
lines.append("# research-agent · 功能点提取验证（读代码结构）")
lines.append("")
lines.append("> 来源：work/targets/research-agent（只读克隆）")
lines.append("> 方式：AST/正则读代码结构，无 LLM；耗时 0.37s")
lines.append("> 总计：**%d** 个功能点（api %d / page %d / component %d）" % (
    len(rows), len(g["api"]), len(g["page"]), len(g["component"])))
lines.append("")
for ftype in ("api", "page", "component"):
    lines.append("## %s（%d）" % (ftype, len(g[ftype])))
    lines.append("")
    for r in g[ftype]:
        lines.append("- `%s` — `%s`" % (r["name"], r["file_path"]))
    lines.append("")

with open("../功能点提取_验证_research-agent.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("written, total", len(rows))
