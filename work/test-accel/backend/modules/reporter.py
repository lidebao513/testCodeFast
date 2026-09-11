"""报告生成：汇总 run 结果 → JSON + HTML（独立产物文件，浅色，便于分享/打开）。"""

import json
import time
from pathlib import Path

from backend.config import PROJECT_ROOT, settings
from backend.db import get_conn


class Reporter:
    # 阶段6（P6-★1）：需向前追溯的「问题状态」——落入失败归因聚类
    PROBLEM_STATUSES = {"fail", "error", "blocked_auth", "structural_only", "blocked_review"}

    def build(self, pid, results, meta=None):
        meta = meta or {}
        total = len(results)

        def cnt(st):
            return sum(1 for r in results if r["status"] == st)

        passed, failed, skipped = cnt("pass"), cnt("fail"), cnt("skipped")
        # 阶段4 批次2（D-★1/★2）新增状态：
        #   structural_only = 服务不可达/未开动态探测，仅完成静态断言（未真测，不计入通过）
        #   blocked_auth    = 真实请求返回 401/403，缺鉴权态（D-②1）
        #   error           = 执行器内部异常（D-★4）
        structural_only, blocked_auth = cnt("structural_only"), cnt("blocked_auth")
        errored, blocked_review = cnt("error"), cnt("blocked_review")

        # —— P6-★1 双向追溯：结果 → 用例 → 测试点 → 功能点 → 源码 ——
        enriched, missing = self._enrich_results(pid, results)

        by_type = {}
        for r in results:
            t = r.get("ctype", "unknown")
            d = by_type.setdefault(t, {"total": 0, "pass": 0, "fail": 0, "skipped": 0})
            d["total"] += 1
            d[r["status"]] = d.get(r["status"], 0) + 1
        # —— P6-★4 失败归因聚合 ——
        failures, by_module = self._failure_clusters(results)
        summary = {
            "total": total,
            "pass": passed,
            "fail": failed,
            "skipped": skipped,
            "structural_only": structural_only,
            "blocked_auth": blocked_auth,
            "error": errored,
            "blocked_review": blocked_review,
            # 真实通过率：分母只算"真正跑过并得出结论"的用例
            "effective_total": passed + failed,
            "by_type": by_type,
            "by_module": by_module,
            "failures": failures,
            "traceability": {
                "enriched": enriched,
                "missing": missing,
                "coverage": round(100.0 * enriched / total, 1) if total else 0.0,
            },
            "project": meta.get("project", ""),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        # —— P6-④ 执行摘要（一句话结论 + 关键指标 + 建议）——
        summary["exec_summary"] = self._exec_summary_core(pid, summary)
        # 用例清册（C-★4）：如导出产物存在则引用其汇总
        proj_name = meta.get("project")
        catalog_card = ""
        if proj_name:
            cat_json = PROJECT_ROOT.parent / f"{proj_name}-test" / "test_cases.json"
            if cat_json.exists():
                try:
                    cat = json.loads(cat_json.read_text(encoding="utf-8"))
                    s = cat.get("summary", {})
                    catalog_card = (
                        f"<div class='card'><b>用例清册：</b>{s.get('count')} 条　"
                        + "类型(正常/异常) "
                        + ", ".join(f"{k}:{v}" for k, v in s.get("by_type", {}).items())
                        + "　"
                        + "测试类型(全量/新增) "
                        + ", ".join(f"{k}:{v}" for k, v in s.get("by_test_type", {}).items())
                        + "　"
                        + "优先级 "
                        + ", ".join(f"{k}:{v}" for k, v in s.get("by_priority", {}).items())
                        + "<br>完整清册见 <code>TEST_CASES.md</code></div>"
                    )
                    summary["test_cases"] = str(cat_json)
                except Exception:
                    pass
        ts = time.strftime("%Y%m%d_%H%M%S")
        # D-★5：报告批次优先复用执行批次号（meta 显式传 > results 内携带 > 时间戳兜底），
        # 使本轮 runs 与 reports 可按 batch_id 关联回溯、对比与识别 flaky。
        batch_id = (
            meta.get("batch_id")
            or (results[0].get("batch_id") if results else None)
            or f"scan_{pid}_{ts}"
        )
        summary["batch_id"] = batch_id
        out_dir = settings.REPORTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / f"scan_{pid}_{ts}.json"
        html_path = out_dir / f"scan_{pid}_{ts}.html"
        json_path.write_text(
            json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        html_path.write_text(
            self._render_html(summary, results, catalog_card, pid), encoding="utf-8"
        )

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO reports (project_id, batch_id, summary, html_path)
               VALUES (?,?,?,?)""",
            (pid, batch_id, json.dumps(summary, ensure_ascii=False), str(html_path)),
        )
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return {
            "id": rid,
            "html_path": str(html_path),
            "json_path": str(json_path),
            "summary": summary,
        }

    def _enrich_results(self, pid, results):
        """P6-★1：把每条执行结果关联到用例/测试点/功能点/源码，挂上追溯字段。

        返回 (enriched, missing) 计数。挂上的字段：
          tp_id / fp_contract_id / module / title / source(源码路径)
        """
        case_ids = [r.get("case_id") for r in results if r.get("case_id")]
        enriched = 0
        if not case_ids:
            return 0, len(results)
        conn = get_conn()
        cur = conn.cursor()
        placeholders = ",".join("?" * len(case_ids))
        cur.execute(
            f"""SELECT c.id, c.tp_id, c.fp_contract_id, c.module AS cmod,
                       c.title AS ctitle, t.source, t.module AS tmod, t.title AS ttitle
                FROM cases c
                LEFT JOIN test_points t ON c.tp_id = t.tp_id AND t.project_id=?
                WHERE c.id IN ({placeholders})""",
            [pid, *case_ids],
        )
        meta_map = {row["id"]: dict(row) for row in cur.fetchall()}
        conn.close()
        for r in results:
            m = meta_map.get(r.get("case_id"))
            if not m:
                r.setdefault("tp_id", None)
                r.setdefault("fp_contract_id", None)
                r.setdefault("module", None)
                r.setdefault("title", None)
                r.setdefault("source", None)
                continue
            r["tp_id"] = m.get("tp_id")
            r["fp_contract_id"] = m.get("fp_contract_id")
            r["module"] = m.get("tmod") or m.get("cmod")
            r["title"] = m.get("ctitle")
            r["source"] = m.get("source")
            enriched += 1
        return enriched, len(results) - enriched

    def _failure_clusters(self, results):
        """P6-★4：失败归因聚合——按状态与模块聚类，给出样例 case_id。"""
        by_status, by_module_raw, clusters = {}, {}, {}
        mod_stats = {}
        for r in results:
            st = r["status"]
            mod = r.get("module") or "未分类"
            d = mod_stats.setdefault(mod, {"total": 0, "pass": 0})
            d["total"] += 1
            if st == "pass":
                d["pass"] += 1
            if st in self.PROBLEM_STATUSES:
                by_status[st] = by_status.get(st, 0) + 1
                by_module_raw[mod] = by_module_raw.get(mod, 0) + 1
                key = (mod, st)
                cl = clusters.setdefault(
                    key, {"module": mod, "status": st, "count": 0, "samples": []}
                )
                cl["count"] += 1
                if len(cl["samples"]) < 5:
                    cl["samples"].append(r.get("case_id"))
        for mod, d in mod_stats.items():
            d["pass_rate"] = round(100.0 * d["pass"] / d["total"], 1) if d["total"] else 0.0
        by_module_sorted = dict(sorted(by_module_raw.items(), key=lambda kv: kv[1], reverse=True))
        cluster_list = sorted(clusters.values(), key=lambda c: c["count"], reverse=True)
        return {
            "total_problem": sum(by_status.values()),
            "by_status": dict(sorted(by_status.items(), key=lambda kv: kv[1], reverse=True)),
            "by_module": by_module_sorted,
            "clusters": cluster_list,
        }, mod_stats

    def _render_html(self, summary, results, catalog_card="", pid=None):
        color = {
            "pass": "#1D9E75",
            "fail": "#E24B4A",
            "skipped": "#BA7517",
            "structural_only": "#6B7785",
            "blocked_auth": "#8B5CF6",
            "error": "#C2410C",
            "blocked_review": "#BA7517",
        }
        rows = []
        for r in results:
            st = r["status"]
            c = color.get(st, "#888")
            reason = r.get("reason") or r.get("log") or ""
            shot = r.get("screenshot_path")
            # P6-★2：失败/浏览器用例证据（截图链接 + 日志详情）
            if shot:
                ev = f"<a href='file:///{shot}' target='_blank' style='color:#2563eb'>截图</a>"
            else:
                ev = "—"
            tp = r.get("tp_id") or "—"
            fp = r.get("fp_contract_id") or "—"
            src = r.get("source") or "—"
            title = (r.get("title") or "").replace("<", "&lt;")
            rows.append(
                f"<tr><td>{r.get('case_id', '')}</td>"
                f"<td>{r.get('module') or '—'}</td>"
                f"<td>{r.get('ctype', '')}</td>"
                f"<td style='color:{c};font-weight:600'>{st}</td>"
                f"<td title='{title}'>{title[:28] or '—'}</td>"
                f"<td><code>{tp}</code></td><td><code>{fp}</code></td>"
                f"<td title='{src}'>{src.split('/')[-1] if src != '—' else '—'}</td>"
                f"<td style='color:{c}'>{reason[:160]}</td><td>{ev}</td>"
                f"<td><details><summary>日志</summary><pre style='white-space:pre-wrap;"
                f"font-size:11px'>{(r.get('log') or '').replace('<', '&lt;')[:600]}</pre></details></td>"
                f"</tr>"
            )
        by_type_html = "".join(
            f"<li><b>{t}</b>: {v['total']} 总计 / {v.get('pass', 0)} 通过 / "
            f"{v.get('fail', 0)} 失败 / {v.get('skipped', 0)} 跳过</li>"
            for t, v in summary["by_type"].items()
        )
        # P6-★4：失败归因卡片
        fl = summary.get("failures", {})
        by_status_html = (
            "".join(f"<li><b>{k}</b>: {v}</li>" for k, v in fl.get("by_status", {}).items())
            or "<li>无</li>"
        )
        clusters_html = (
            "".join(
                f"<li><span style='color:{color.get(c['status'], '#888')}'>"
                f"[{c['status']}]</span> <b>{c['module']}</b>：{c['count']} 条"
                f"　样例 case_id={c['samples']}</li>"
                for c in fl.get("clusters", [])[:15]
            )
            or "<li>无</li>"
        )
        by_module_html = (
            "".join(
                f"<li><b>{m}</b>: 通过率 {d['pass_rate']}% ({d['pass']}/{d['total']})</li>"
                for m, d in summary.get("by_module", {}).items()
                if d["total"] >= 3
            )
            or "<li>无</li>"
        )
        tr = summary.get("traceability", {})
        trace_html = (
            f"已关联 {tr.get('enriched', 0)}/{tr.get('enriched', 0) + tr.get('missing', 0)}"
            f" 条（覆盖率 {tr.get('coverage', 0)}%）"
        )
        # —— P6-④ 执行摘要卡片 ——
        es = summary.get("exec_summary") or {}
        exec_html = ""
        if es:
            bullets = "".join(f"<li>{b}</li>" for b in es.get("bullets", []))
            exec_html = (
                f"<div class='exec'>"
                f"<b>📌 执行摘要（一句话结论）</b><br>"
                f"<div style='font-size:15px;font-weight:600;margin:6px 0;color:#1a1a1a'>"
                f"{es.get('headline', '')}</div>"
                f"<ul style='margin:6px 0 2px 18px'>{bullets}</ul>"
                f"<div style='font-size:12px;color:#5a6570'>"
                f"趋势：{es.get('trend', '—')}　覆盖率：FP {es.get('fp_rate')}% / TP {es.get('tp_rate')}%"
                f"　Flaky：{es.get('flaky', 0)} 条</div></div>"
            )
        return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>测试报告 · {summary["project"]}</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:32px;color:#1a1a1a;}}
h1{{font-size:20px;}} h3{{margin-top:24px;}} .card{{background:#f6f7f9;border:1px solid #e3e6ea;border-radius:10px;padding:16px;margin:12px 0;}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;}} .kpi{{flex:1;min-width:90px;text-align:center;background:#fff;border:1px solid #e3e6ea;border-radius:10px;padding:14px;}}
.kpi .n{{font-size:26px;font-weight:600;}} table{{width:100%;border-collapse:collapse;margin-top:8px;}}
th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #eee;font-size:12.5px;vertical-align:top;}}
th{{background:#f0f2f5;position:sticky;top:0;}} code{{font-size:11px;color:#555;}}
pre{{margin:0;}} a{{text-decoration:none;}}
.exec{{background:#EAF2FF;border:1px solid #B9D4FF;border-left:4px solid #2563EB;border-radius:10px;padding:14px 16px;margin:12px 0;font-size:13px;line-height:1.7;}}</style></head>
<body><h1>测试加速平台 · 扫描测试报告</h1>
<div class="card"><b>项目：</b>{summary["project"]}　<b>生成时间：</b>{summary["generated_at"]}　<b>批次：</b>{summary.get("batch_id", "")}</div>
{exec_html}
<div class="kpis">
<div class="kpi"><div class="n">{summary["total"]}</div>总用例</div>
<div class="kpi"><div class="n" style="color:#1D9E75">{summary["pass"]}</div>通过</div>
<div class="kpi"><div class="n" style="color:#E24B4A">{summary["fail"]}</div>失败</div>
<div class="kpi"><div class="n" style="color:#BA7517">{summary["skipped"]}</div>跳过</div>
<div class="kpi"><div class="n" style="color:#6B7785">{summary.get("structural_only", 0)}</div>仅静态验证</div>
<div class="kpi"><div class="n" style="color:#8B5CF6">{summary.get("blocked_auth", 0)}</div>需鉴权</div>
<div class="kpi"><div class="n" style="color:#C2410C">{summary.get("error", 0)}</div>执行异常</div>
</div>
<div class="card" style="font-size:13px;color:#5a6570">
<b>口径说明：</b>「通过/失败」仅统计<strong>真实执行并得出结论</strong>的用例；
「仅静态验证」指服务不可达或未开启动态探测，只做了源码结构断言（<strong>未发出真实请求，不计为通过</strong>）；
「需鉴权」指真实请求返回 401/403，当前执行未携带 token。真实通过率 = {summary["pass"]} / {summary.get("effective_total", 0)}。
</div>
{catalog_card}
<div class="card"><b>双向追溯覆盖：</b>{trace_html}（结果 → 用例 → 测试点 → 功能点 → 源码）</div>
<div class="card"><b>按类型：</b><ul>{by_type_html}</ul></div>
<div class="card"><b>失败归因（按状态）：</b><ul>{by_status_html}</ul>
<b>失败归因（按模块 TOP）：</b><ul>{by_module_html}</ul>
<b>失败聚类（模块 × 状态，样例 case_id）：</b><ul>{clusters_html}</ul></div>
<h3>明细（含追溯与证据）</h3>
<table>
<tr><th>Case</th><th>模块</th><th>类型</th><th>状态</th><th>用例标题</th><th>测试点</th><th>功能点</th><th>源码</th><th>说明</th><th>证据</th><th>日志</th></tr>
{"".join(rows)}</table>
</body></html>"""

    # ------------------------------------------------------------------
    # P6-④ 执行摘要（一句话结论 + 关键指标 + 建议）
    # ------------------------------------------------------------------
    def _exec_summary_core(self, pid, summary):
        """基于单份报告 summary + 跨批分析（趋势/flaky/覆盖率）生成给 PM/领导的结论。

        返回 {headline, bullets, metrics, trend, fp_rate, tp_rate, flaky}。
        """
        from backend.modules import analytics as am

        tr = am.trend(pid)
        fl = am.flaky(pid)
        cov = am.coverage(pid)

        total = summary.get("total", 0)
        passed = summary.get("pass", 0)
        failed = summary.get("fail", 0)
        eff = summary.get("effective_total", passed + failed)
        pr = round(100.0 * passed / eff, 1) if eff else None
        so = summary.get("structural_only", 0)
        ba = summary.get("blocked_auth", 0)
        er = summary.get("error", 0)
        br = summary.get("blocked_review", 0)
        tp_total = cov.get("tp_total", 0)
        tp_cov = cov.get("tp_covered", 0)
        tp_rate = cov.get("tp_rate", 0)
        fp_rate = cov.get("fp_rate", 0)
        flaky_n = fl.get("flaky_count", 0)
        direction = tr.get("pass_rate_direction", "stable")

        bullets = []
        if total > 0 and so == total:
            headline = (
                f"本轮 {total} 条用例全部完成执行，但均处于「静态结构验证」状态"
                f"（未发起真实请求），暂无可信通过率结论。"
            )
            bullets.append(
                f"通过 {passed} / 失败 {failed} / 仅静态验证 {so} / 需鉴权 {ba} / 执行异常 {er}。"
            )
            bullets.append(
                "建议：启动真实被测服务并开启动态探测（ENABLE_DYNAMIC_PROBE=on），"
                "以产生真实通过率与失败证据。"
            )
        elif eff == 0:
            headline = f"本轮 {total} 条用例无真实执行结论（有效执行数为 0）。"
            bullets.append(f"仅静态验证 {so} / 需鉴权 {ba} / 执行异常 {er}。")
        else:
            if pr is not None and pr >= 90:
                headline = f"整体健康：真实通过率 {pr}%（{passed}/{eff}），失败较少。"
            elif pr is not None and pr >= 60:
                headline = f"基本可用：真实通过率 {pr}%（{passed}/{eff}），存在部分失败需关注。"
            else:
                headline = (
                    f"存在问题：真实通过率仅 {pr}%（{passed}/{eff}），失败较多，建议优先排查。"
                )
            bullets.append(
                f"通过 {passed} / 失败 {failed} / 仅静态验证 {so} / 需鉴权 {ba} / 执行异常 {er}。"
            )

        if ba > 0:
            bullets.append(
                f"需鉴权 {ba} 条（返回 401/403），建议配置 AUTH_AUTO_LOGIN 自动注入 token。"
            )
        if er > 0:
            bullets.append(f"执行异常 {er} 条，建议检查执行器日志定位内部错误。")
        if br > 0:
            bullets.append(f"评审阻塞 {br} 条（待人工 review 放行），建议走 review 流程。")

        fl_data = summary.get("failures", {})
        clusters = fl_data.get("clusters", [])[:3]
        if clusters:
            bullets.append(
                "失败 TOP："
                + "；".join(f"{c['module']} [{c['status']}] {c['count']} 条" for c in clusters)
            )
        if tp_rate < 100:
            bullets.append(
                f"测试点覆盖率 {tp_rate}%（{tp_cov}/{tp_total}），存在未覆盖测试点，建议补用例。"
            )

        if direction == "regressing":
            bullets.append("趋势：通过率较上次退化（regressing），建议关注退化原因。")
        elif direction == "improving":
            bullets.append("趋势：通过率较上次改善（improving）。")
        else:
            bullets.append("趋势：通过率平稳（stable）。")

        if flaky_n > 0:
            bullets.append(
                f"发现 {flaky_n} 个不稳定（flaky）用例，建议加固（加重试 / 隔离外部依赖）。"
            )
        else:
            bullets.append("未检测到不稳定（flaky）用例。")

        return {
            "headline": headline,
            "bullets": bullets,
            "metrics": {
                "total": total,
                "pass": passed,
                "fail": failed,
                "effective_total": eff,
                "pass_rate": pr,
                "structural_only": so,
                "blocked_auth": ba,
                "error": er,
                "blocked_review": br,
            },
            "trend": direction,
            "fp_rate": fp_rate,
            "tp_rate": tp_rate,
            "flaky": flaky_n,
        }

    def build_exec_summary(self, pid, rid=None):
        """取报告（指定 rid 或该项目最新一份）并生成执行摘要；报告不存在返回 None。"""
        if rid is not None:
            d = self.build_report_detail(pid, rid, inline=False)
            if d is None:
                return None
            summary = d.get("summary", {})
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT summary FROM reports WHERE project_id=? ORDER BY id DESC LIMIT 1", (pid,)
            )
            row = cur.fetchone()
            conn.close()
            if not row or not row["summary"]:
                return None
            summary = json.loads(row["summary"])
        return self._exec_summary_core(pid, summary)

    def build_report_detail(self, pid, rid, inline=False):
        """P6-★3：从 reports 表取回单条报告（summary / html_path / html 全文）。"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports WHERE id=? AND project_id=?", (rid, pid))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        r = dict(row)
        out = {
            "id": r["id"],
            "project_id": r["project_id"],
            "batch_id": r.get("batch_id"),
            "created_at": str(r.get("created_at")),
            "html_path": r.get("html_path"),
            "summary": json.loads(r["summary"]) if r.get("summary") else {},
        }
        if inline:
            try:
                out["html"] = Path(r["html_path"]).read_text(encoding="utf-8")
            except Exception:
                out["html"] = None
        return out

    def build_rich(self, pid, context, meta=None):
        """富版报告：用 test_report.html 模板渲染一份结构化 HTML 报告并落盘。

        context: 模板 {{token}} 占位符覆盖字典（缺省回退到示例数据）。
        meta: 写入 reports 表的摘要 JSON（可选）。
        与 build() 并存，不改动既有简版 HTML 生成逻辑。
        """
        from backend.modules.html_report import render_report

        ts = time.strftime("%Y%m%d_%H%M%S")
        out_dir = settings.REPORTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / f"rich_{pid}_{ts}.html"
        html_path.write_text(render_report(context), encoding="utf-8")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO reports (project_id, batch_id, summary, html_path)
               VALUES (?,?,?,?)""",
            (pid, f"rich_{pid}_{ts}", json.dumps(meta or {}, ensure_ascii=False), str(html_path)),
        )
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return {"id": rid, "html_path": str(html_path)}


reporter = Reporter()
