"""报告生成：汇总 run 结果 → JSON + HTML（独立产物文件，浅色，便于分享/打开）。"""
import json
import time
from pathlib import Path
from backend.db import get_conn
from backend.config import settings


class Reporter:
    def build(self, pid, results, meta=None):
        meta = meta or {}
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "pass")
        failed = sum(1 for r in results if r["status"] == "fail")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        by_type = {}
        for r in results:
            t = r.get("ctype", "unknown")
            d = by_type.setdefault(t, {"total": 0, "pass": 0, "fail": 0, "skipped": 0})
            d["total"] += 1
            d[r["status"]] = d.get(r["status"], 0) + 1
        summary = {
            "total": total, "pass": passed, "fail": failed, "skipped": skipped,
            "by_type": by_type,
            "project": meta.get("project", ""),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = settings.REPORTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / f"scan_{pid}_{ts}.json"
        html_path = out_dir / f"scan_{pid}_{ts}.html"
        json_path.write_text(
            json.dumps({"summary": summary, "results": results},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        html_path.write_text(self._render_html(summary, results), encoding="utf-8")

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO reports (project_id, batch_id, summary, html_path)
               VALUES (?,?,?,?)""",
            (pid, f"scan_{pid}_{ts}", json.dumps(summary, ensure_ascii=False), str(html_path)))
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return {"id": rid, "html_path": str(html_path), "json_path": str(json_path),
                "summary": summary}

    def _render_html(self, summary, results):
        color = {"pass": "#1D9E75", "fail": "#E24B4A", "skipped": "#BA7517"}
        rows = []
        for r in results:
            c = color.get(r["status"], "#888")
            reason = r.get("reason") or r.get("log") or ""
            rows.append(
                f"<tr><td>{r.get('case_id','')}</td><td>{r.get('ctype','')}</td>"
                f"<td>{r['status']}</td>"
                f"<td style='color:{c};font-weight:500'>{reason}</td></tr>")
        by_type_html = "".join(
            f"<li><b>{t}</b>: {v['total']} 总计 / {v.get('pass',0)} 通过 / "
            f"{v.get('fail',0)} 失败 / {v.get('skipped',0)} 跳过</li>"
            for t, v in summary["by_type"].items())
        return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>测试报告 · {summary['project']}</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:32px;color:#1a1a1a;}}
h1{{font-size:20px;}} .card{{background:#f6f7f9;border:1px solid #e3e6ea;border-radius:10px;padding:16px;margin:12px 0;}}
.kpis{{display:flex;gap:12px;}} .kpi{{flex:1;text-align:center;background:#fff;border:1px solid #e3e6ea;border-radius:10px;padding:14px;}}
.kpi .n{{font-size:26px;font-weight:600;}} table{{width:100%;border-collapse:collapse;margin-top:8px;}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #eee;font-size:13px;}}</style></head>
<body><h1>测试加速平台 · 扫描测试报告</h1>
<div class="card"><b>项目：</b>{summary['project']}　<b>生成时间：</b>{summary['generated_at']}</div>
<div class="kpis">
<div class="kpi"><div class="n">{summary['total']}</div>总用例</div>
<div class="kpi"><div class="n" style="color:#1D9E75">{summary['pass']}</div>通过</div>
<div class="kpi"><div class="n" style="color:#E24B4A">{summary['fail']}</div>失败</div>
<div class="kpi"><div class="n" style="color:#BA7517">{summary['skipped']}</div>跳过</div>
</div>
<div class="card"><b>按类型：</b><ul>{by_type_html}</ul></div>
<h3>明细</h3><table><tr><th>Case</th><th>类型</th><th>状态</th><th>说明</th></tr>{''.join(rows)}</table>
</body></html>"""


reporter = Reporter()
