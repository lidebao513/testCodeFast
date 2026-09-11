"""章节化全功能验证报告（P6-②5 落地 / 阶段6 批次4）。

按历史验证报告风格输出 9 章节（变更摘要→测试点→用例清册→明细→统计→结论风险→
监控→截图→复用占比），同时产出 VERIFICATION_REPORT.md 与 VERIFICATION_REPORT.html。

对应能力编号：
  6.1 报告数据聚合  —— aggregate(pid)：变更面/测试点/用例清册/执行结果/统计/截图
  6.2 报告模板渲染 —— render_html()：report_templates/verification_report.html {{token}} 替换
  6.3 章节化输出   —— render_md()：9 章节 Markdown
  6.4 最终交付     —— generate()：MD + HTML（截图 base64 内嵌）落盘

数据全部来自平台 DB（functional_points / test_points / cases / runs / run_batches /
change_log），不依赖外部脚本。
"""

from __future__ import annotations

import base64
import json
import time
from collections import Counter, OrderedDict
from pathlib import Path

from backend.config import settings
from backend.db import get_conn


TEMPLATE = Path(__file__).resolve().parents[2] / "report_templates" / "verification_report.html"

# 结果状态 → (展示名, 是否算通过, badge class)
_STATUS_MAP = {
    "pass": ("PASS", True, "pass"),
    "structural_only": ("仅静态断言", None, "warn"),  # 未参与动态通过/失败判定
    "blocked_auth": ("鉴权阻断", None, "warn"),
    "blocked_review": ("待审批", None, "warn"),
    "skipped": ("跳过", None, "warn"),
    "fail": ("FAIL", False, "fail"),
    "error": ("异常", False, "fail"),
}


def _esc(s):
    return (
        str(s if s is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _md_escape(s):
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


def _md_table(rows, header):
    out = "| " + " | ".join(header) + " |\n"
    out += "|" + "|".join(["---"] * len(header)) + "|\n"
    for r in rows:
        out += "| " + " | ".join(_md_escape(c) for c in r) + " |\n"
    return out


# ---------------------------------------------------------------- 6.1 聚合
def aggregate(pid: int, batch_id: str | None = None) -> dict:
    """聚合 9 章节所需全部数据（6.1）。batch_id 缺省取该项目最近一个批次。"""
    conn = get_conn()
    cur = conn.cursor()

    # --- 基础量 ---
    fps_total = cur.execute(
        "SELECT COUNT(*) FROM functional_points WHERE project_id=?", (pid,)
    ).fetchone()[0]
    tps = cur.execute(
        "SELECT tp_id, module, title, dimension, method, expect FROM test_points "
        "WHERE project_id=? ORDER BY module, tp_id",
        (pid,),
    ).fetchall()
    cases = cur.execute(
        """SELECT c.id, c.title, c.module, c.case_type, c.steps, c.status,
                  c.last_result, c.tp_id, t.title AS tp_title, t.expect AS expect
           FROM cases c LEFT JOIN test_points t
             ON t.project_id=c.project_id AND t.tp_id=c.tp_id
           WHERE c.project_id=? AND COALESCE(c.status,'') NOT IN ('obsolete','archived')
           ORDER BY c.module, c.id""",
        (pid,),
    ).fetchall()

    # --- 变更面（change_log 最近一条）---
    cl = cur.execute(
        """SELECT commit_from, commit_to, new_fp_ids, updated_fp_ids, removed_fp_ids, created_at
           FROM change_log WHERE project_id=? ORDER BY created_at DESC LIMIT 1""",
        (pid,),
    ).fetchone()
    change = None
    if cl:

        def _ids(s):
            try:
                v = json.loads(s) if s else []
            except Exception:
                v = []
            return v if isinstance(v, list) else []

        change = {
            "commit_from": cl["commit_from"],
            "commit_to": cl["commit_to"],
            "created_at": cl["created_at"],
            "new": len(_ids(cl["new_fp_ids"])),
            "updated": len(_ids(cl["updated_fp_ids"])),
            "removed": len(_ids(cl["removed_fp_ids"])),
        }

    # --- 执行批次选择 ---
    if batch_id:
        b = cur.execute(
            "SELECT * FROM run_batches WHERE batch_id=? AND project_id=?", (batch_id, pid)
        ).fetchone()
    else:
        b = cur.execute(
            "SELECT * FROM run_batches WHERE project_id=? ORDER BY started_at DESC LIMIT 1", (pid,)
        ).fetchone()
    batch = dict(b) if b else None

    runs = []
    if batch:
        runs = cur.execute(
            """SELECT r.id, r.case_id, r.status, r.duration_ms, r.screenshot_path, r.log_path,
                      c.title AS case_title, c.module, c.case_type
               FROM runs r LEFT JOIN cases c ON c.id=r.case_id
               WHERE r.project_id=? AND r.batch_id=? ORDER BY r.id""",
            (pid, batch["batch_id"]),
        ).fetchall()

    # --- 监控时间线（最近 12 批）---
    monitor = cur.execute(
        """SELECT batch_id, state, started_at, finished_at, total, done, status_counts
           FROM run_batches WHERE project_id=? ORDER BY started_at DESC LIMIT 12""",
        (pid,),
    ).fetchall()

    # --- 用例生命周期（复用占比口径）---
    lifecycle = {
        r[0]: r[1]
        for r in cur.execute(
            "SELECT COALESCE(status,'(未标记)'), COUNT(*) FROM cases WHERE project_id=? GROUP BY status",
            (pid,),
        )
    }
    test_type = {
        r[0]: r[1]
        for r in cur.execute(
            "SELECT COALESCE(test_type,'(未标记)'), COUNT(*) FROM cases WHERE project_id=? GROUP BY test_type",
            (pid,),
        )
    }
    conn.close()

    # --- 统计（基于所选批次 runs）---
    status_counter = Counter(r["status"] for r in runs)
    n_pass = status_counter.get("pass", 0)
    n_fail = status_counter.get("fail", 0) + status_counter.get("error", 0)
    n_judged = n_pass + n_fail

    by_module = OrderedDict()
    by_type = OrderedDict()
    for r in runs:
        m = r["module"] or "(未分模块)"
        t = r["case_type"] or "(未标注)"
        st = _STATUS_MAP.get(r["status"], (r["status"], None, "warn"))[1]
        by_module.setdefault(m, {"pass": 0, "fail": 0, "other": 0})
        by_type.setdefault(t, {"pass": 0, "fail": 0, "other": 0})
        key = "pass" if st else ("fail" if st is False else "other")
        by_module[m][key] += 1
        by_type[t][key] += 1

    # --- 截图（6.4）：runs 内截图 + 指定目录补充 ---
    shots = []
    seen = set()
    for r in runs:
        p = r["screenshot_path"]
        if p and p not in seen and Path(p).exists():
            seen.add(p)
            shots.append(
                {
                    "id": f"run-{r['id']}",
                    "label": r["case_title"] or f"run #{r['id']}",
                    "path": p,
                    "ok": True,
                }
            )
    shot_dir = settings.SCREENSHOTS_DIR
    if shot_dir.exists():
        for p in sorted(shot_dir.glob("*.png")):
            if str(p) not in seen:
                seen.add(str(p))
                shots.append({"id": p.stem, "label": p.stem, "path": str(p), "ok": True})

    return {
        "pid": pid,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "fps_total": fps_total,
        "tps": [dict(t) for t in tps],
        "cases": [dict(c) for c in cases],
        "change": change,
        "batch": batch,
        "runs": [dict(r) for r in runs],
        "status_counter": dict(status_counter),
        "n_pass": n_pass,
        "n_fail": n_fail,
        "n_judged": n_judged,
        "by_module": by_module,
        "by_type": by_type,
        "monitor": [dict(m) for m in monitor],
        "lifecycle": lifecycle,
        "test_type": test_type,
        "shots": shots,
    }


# ---------------------------------------------------------------- 6.2 HTML 渲染
def render_html(d: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    pid = d["pid"]

    n_cases = len(d["cases"])
    n_tps = len(d["tps"])
    ch = d.get("change")
    kpi_change = f"{ch['new']}/{ch['updated']}/{ch['removed']}" if ch else "—"

    meta = (
        f"项目 #{pid} ｜ 生成时间 {d['generated_at']} ｜ "
        f"批次 {d['batch']['batch_id'] if d['batch'] else '（无执行批次）'}"
        + (f" ｜ 变更 {ch['commit_from']} → {ch['commit_to']}" if ch else "")
    )

    # 一、变更摘要
    if ch:
        section_change = (
            f"<p class='sec'>最近一次代码变更对账（{ch['created_at']}）：<b>"
            f"{ch['commit_from']} → {ch['commit_to']}</b>，功能点 "
            f"<span class='pass'>+{ch['new']} 新增</span> / "
            f"<span class='warn'>{ch['updated']} 更新</span> / "
            f"<span class='fail'>-{ch['removed']} 移除</span>。"
            f"用例状态已按 C-②8 增量对账与代码变更保持一致（updated/obsolete/reused）。</p>"
        )
    else:
        section_change = (
            "<p class='sec'>暂无变更对账记录（可调用 <code>/diff_analyze</code> 生成）。"
            "以下内容基于当前代码基线全量生成。</p>"
        )

    # 二、测试点（415 全量太大时按模块聚合并抽样展示？——保留全量，与清册一致）
    tp_rows = []
    for t in d["tps"]:
        tp_rows.append(
            f"<tr><td>{_esc(t['module'])}</td><td>{_esc(t['title'])}</td>"
            f"<td><span class='tag'>{_esc(t['dimension'])}</span></td>"
            f"<td>{_esc(t['method'])}</td><td class='step'>{_esc(t['expect'])}</td></tr>"
        )
    testpoints_body = "\n".join(tp_rows)

    # 三、用例清册
    case_rows = []
    for c in d["cases"]:
        lr = c["last_result"] or "—"
        lr_cls = _STATUS_MAP.get(lr, ("—", None, "warn"))[2]
        case_rows.append(
            f"<tr><td><code>{_esc(c['id'])}</code></td><td>{_esc(c['module'])}</td>"
            f"<td>{_esc(c['tp_title'] or c['title'])}</td>"
            f"<td><span class='tag'>{_esc(c['case_type'])}</span></td>"
            f"<td class='step'>{_esc(c['steps'])}</td><td class='step'>{_esc(c['expect'])}</td>"
            f"<td>{_esc(c['status'])}</td><td><span class='badge {lr_cls}'>{_esc(lr)}</span></td></tr>"
        )
    cases_body = "\n".join(case_rows)

    # 四、明细与执行结果
    sc = d["status_counter"]
    if d["batch"]:
        head = (
            f"<p class='sec'>批次 <code>{_esc(d['batch']['batch_id'])}</code>"
            f"（{_esc(d['batch']['started_at'])} ~ {_esc(d['batch']['finished_at'] or '进行中')}），"
            f"共 {len(d['runs'])} 条执行记录。状态分布："
            + "、".join(
                f"{_STATUS_MAP.get(k, (k, None, 'warn'))[0]}×{v}" for k, v in sorted(sc.items())
            )
            + "。</p>"
        )
        run_rows = []
        for r in d["runs"]:
            name, _ok, cls = _STATUS_MAP.get(r["status"], (r["status"], None, "warn"))
            dur = f"{r['duration_ms'] / 1000:.1f}s" if r["duration_ms"] else "—"
            shot = "✅" if (r["screenshot_path"] and Path(r["screenshot_path"]).exists()) else "—"
            run_rows.append(
                f"<tr><td><code>{_esc(r['case_id'])}</code></td><td>{_esc(r['case_title'])}</td>"
                f"<td>{_esc(r['module'])}</td><td><span class='badge {cls}'>{name}</span></td>"
                f"<td>{dur}</td><td>{shot}</td></tr>"
            )
        section_detail = (
            head + "<table><tr><th>CaseID</th><th>用例</th><th>模块</th>"
            "<th>结果</th><th>耗时</th><th>截图</th></tr>" + "\n".join(run_rows) + "</table>"
        )
    else:
        section_detail = (
            "<p class='sec'>暂无执行批次。用例清册见第三章；"
            "执行后本节将展示逐条明细（结果/耗时/截图）。</p>"
        )

    # 五、统计
    rate_txt = f"{d['n_pass'] / d['n_judged'] * 100:.1f}%" if d["n_judged"] else "—"
    stats_overall_body = "\n".join(
        [
            f"<tr><td>本轮批次（判定类结果）</td><td class='pass'>{d['n_pass']}</td>"
            f"<td class='fail'>{d['n_fail']}</td><td>通过率 {rate_txt}</td></tr>",
            f"<tr><td>环境态（阻断/静态/跳过/待审批）</td><td class='warn'>{sum(v for k, v in sc.items() if _STATUS_MAP.get(k, (k, None, 'warn'))[1] is None)}</td>"
            f"<td>—</td><td>不计入通过/失败判定</td></tr>",
            f"<tr><td>用例清册 / 测试点 / 功能点</td><td>{n_cases}</td><td>—</td>"
            f"<td>{n_tps} 测试点 / {d['fps_total']} 功能点</td></tr>",
        ]
    )
    sm = []
    for m, v in d["by_module"].items():
        total = v["pass"] + v["fail"]
        sm.append(
            f"<tr><td>{_esc(m)}</td><td class='pass'>{v['pass']}</td>"
            f"<td class='fail'>{v['fail']}</td>"
            f"<td>{(v['pass'] / total * 100 if total else 0):.0f}%</td></tr>"
        )
    stats_module_body = "\n".join(sm) or "<tr><td colspan='4'>暂无执行数据</td></tr>"
    st = []
    for t, v in d["by_type"].items():
        total = v["pass"] + v["fail"]
        st.append(
            f"<tr><td>{_esc(t)}</td><td class='pass'>{v['pass']}</td>"
            f"<td class='fail'>{v['fail']}</td>"
            f"<td>{(v['pass'] / total * 100 if total else 0):.0f}%</td></tr>"
        )
    stats_type_body = "\n".join(st) or "<tr><td colspan='4'>暂无执行数据</td></tr>"

    # 六、结论与风险
    if d["n_judged"]:
        concl = (
            f"<p><b>结论：</b>批次判定类结果 {d['n_pass']} PASS / {d['n_fail']} FAIL"
            f"（通过率 {rate_txt}）。"
            + (
                "全部判定类用例通过，无失败证据。"
                if d["n_fail"] == 0
                else "存在失败项，详见第四章明细与失败归因报告。"
            )
            + "</p>"
        )
    else:
        concl = (
            "<p><b>结论：</b>本批次全部为环境态结果（仅静态断言/鉴权阻断等），"
            "暂无可信动态通过率结论；挂起被测服务后重新执行即可获得真实 pass/fail。</p>"
        )
    risks = []
    if sc.get("blocked_auth"):
        risks.append(
            f"<li><b>鉴权阻断 {sc['blocked_auth']} 条</b>：需配置测试账号/凭据后补跑。</li>"
        )
    if sc.get("structural_only"):
        risks.append(
            f"<li><b>仅静态断言 {sc['structural_only']} 条</b>：动态探测未覆盖，结果不代表运行时行为。</li>"
        )
    if sc.get("blocked_review"):
        risks.append(
            f"<li><b>待审批 {sc['blocked_review']} 条</b>：REVIEW_GATE 开启，需先完成用例审批。</li>"
        )
    if ch and (ch["new"] or ch["removed"]):
        risks.append(
            f"<li><b>变更面未清零</b>：{ch['new']} 新增 / {ch['removed']} 移除功能点，"
            "建议确认对账后用例与最新代码一致。</li>"
        )
    if not d["shots"]:
        risks.append("<li><b>无执行截图</b>：动态执行未产出浏览器截图，证据链待补。</li>")
    risks_body = "<ol>" + "".join(risks) + "</ol>" if risks else "<p>未识别到显著风险。</p>"
    section_conclusion = concl + "<p><b>风险与建议：</b></p>" + risks_body

    # 七、监控
    mon_rows = []
    for m in d["monitor"]:
        try:
            dist = json.loads(m["status_counts"]) if m["status_counts"] else {}
        except Exception:
            dist = {}
        dist_txt = "、".join(
            f"{_STATUS_MAP.get(k, (k, None, 'warn'))[0]}×{v}" for k, v in sorted(dist.items())
        )
        mon_rows.append(
            f"<tr><td><code>{_esc(m['batch_id'])}</code></td><td>{_esc(m['state'])}</td>"
            f"<td>{_esc(m['started_at'])}</td><td>{_esc(m['finished_at'] or '—')}</td>"
            f"<td>{m['done']}/{m['total']}</td><td>{dist_txt}</td></tr>"
        )
    monitor_body = "\n".join(mon_rows) or "<tr><td colspan='6'>暂无批次记录</td></tr>"

    # 八、截图（base64 内嵌，6.4）
    shot_cards = []
    for s in d["shots"][:60]:  # 上限 60 张防体积失控
        try:
            b = base64.b64encode(Path(s["path"]).read_bytes()).decode("ascii")
            shot_cards.append(
                f"<div class='shot'><div class='shot-h'><b>{_esc(s['id'])}</b> {_esc(s['label'])}</div>"
                f"<img src='data:image/png;base64,{b}' alt='{_esc(s['id'])}'></div>"
            )
        except Exception:
            shot_cards.append(
                f"<div class='shot'><div class='shot-h'><b>{_esc(s['id'])}</b> 截图读取失败</div></div>"
            )
    n_shots = len(shot_cards)
    if n_shots:
        section_shots = (
            f"<p class='sec'>以下截图取自平台执行产物（data/screenshots 与 runs 记录），"
            f"佐证「页面已渲染 / 回复已生成」。最多内嵌 60 张，当前内嵌 {n_shots} 张。</p>"
            f"<div class='shots'>{''.join(shot_cards)}</div>"
        )
    else:
        section_shots = (
            "<p class='sec'>暂无截图。动态执行（含浏览器步骤）完成后，"
            "本节将内嵌展示每条用例的界面证据。</p>"
        )

    # 九、复用占比
    tt = d["test_type"]
    n_total = sum(v for k, v in tt.items() if k not in ("(未标记)",))
    n_new = tt.get("新增", 0)
    n_reuse = max(n_total - n_new, 0)
    reuse_rate = f"{n_reuse / n_total * 100:.1f}%" if n_total else "—"
    reuse_body = (
        f"<tr><td>用例资产（对账后）</td><td class='pass'>{n_reuse}（沿用+更新）</td>"
        f"<td>{n_new}（新增）</td><td>{reuse_rate}</td></tr>"
    )
    lc = d["lifecycle"]
    section_reuse_note = (
        f"<div class='note'>生命周期分布：generated×{lc.get('generated', 0)} / "
        f"updated×{lc.get('updated', 0)} / obsolete×{lc.get('obsolete', 0)}（obsolete 不进入执行与导出）。"
        f"严格遵循「使用已有用例、代码变更才更新」的对账铁律。</div>"
    )

    tokens = {
        "report_title": f"全功能验证报告 · 项目 #{pid}",
        "report_meta_line": meta,
        "kpi_cases": n_cases,
        "kpi_tps": n_tps,
        "kpi_fps": d["fps_total"],
        "kpi_pass": d["n_pass"],
        "kpi_fail": d["n_fail"],
        "kpi_change": kpi_change,
        "kpi_shots": n_shots,
        "section_change": section_change,
        "testpoints_body": testpoints_body,
        "cases_body": cases_body,
        "section_detail": section_detail,
        "stats_overall_body": stats_overall_body,
        "stats_module_body": stats_module_body,
        "stats_type_body": stats_type_body,
        "section_conclusion": section_conclusion,
        "monitor_body": monitor_body,
        "section_shots": section_shots,
        "reuse_body": reuse_body,
        "section_reuse_note": section_reuse_note,
    }
    for k, v in tokens.items():
        tpl = tpl.replace(f"{{{{{k}}}}}", str(v))
    return tpl


# ---------------------------------------------------------------- 6.3 MD 渲染
def render_md(d: dict) -> str:
    pid = d["pid"]
    L = []
    L.append(f"# 全功能验证报告 · 项目 #{pid}\n")
    ch = d.get("change")
    L.append(
        f"> 生成时间：{d['generated_at']} ｜ "
        f"批次：`{d['batch']['batch_id'] if d['batch'] else '（无）'}` ｜ "
        f"用例 {len(d['cases'])} / 测试点 {len(d['tps'])} / 功能点 {d['fps_total']}\n"
    )

    L.append("## 一、变更摘要\n")
    if ch:
        L.append(
            f"最近对账：`{ch['commit_from']}` → `{ch['commit_to']}`（{ch['created_at']}），"
            f"功能点 **+{ch['new']} 新增 / {ch['updated']} 更新 / -{ch['removed']} 移除**。"
            "用例状态已按增量对账与代码保持一致。\n"
        )
    else:
        L.append("暂无变更对账记录（可调用 `/diff_analyze` 生成）。\n")

    L.append("## 二、测试点设计（按模块）\n")
    L.append(
        _md_table(
            [(t["module"], t["title"], t["dimension"], t["method"], t["expect"]) for t in d["tps"]],
            ["模块", "测试点", "维度", "方式", "预期"],
        )
    )

    L.append(f"\n## 三、完整测试用例清单（{len(d['cases'])} 条）\n")
    L.append(
        _md_table(
            [
                (
                    c["id"],
                    c["module"],
                    c["tp_title"] or c["title"],
                    c["case_type"],
                    c["steps"],
                    c["expect"],
                    c["status"],
                    c["last_result"] or "—",
                )
                for c in d["cases"]
            ],
            ["ID", "模块", "测试点", "类型", "步骤", "预期", "状态", "最近结果"],
        )
    )

    L.append("\n## 四、用例明细与执行结果\n")
    if d["batch"]:
        L.append(
            f"批次 `{d['batch']['batch_id']}`（{d['batch']['started_at']}），共 {len(d['runs'])} 条执行。\n"
        )
        L.append(
            _md_table(
                [
                    (
                        r["case_id"],
                        r["case_title"],
                        r["module"],
                        _STATUS_MAP.get(r["status"], (r["status"],))[0],
                        f"{r['duration_ms'] / 1000:.1f}s" if r["duration_ms"] else "—",
                        "有"
                        if (r["screenshot_path"] and Path(r["screenshot_path"]).exists())
                        else "—",
                    )
                    for r in d["runs"]
                ],
                ["CaseID", "用例", "模块", "结果", "耗时", "截图"],
            )
        )
    else:
        L.append("暂无执行批次。\n")

    L.append("\n## 五、通过 / 失败统计\n")
    rate = f"{d['n_pass'] / d['n_judged'] * 100:.1f}%" if d["n_judged"] else "—"
    sc = d["status_counter"]
    n_other = sum(v for k, v in sc.items() if _STATUS_MAP.get(k, ("", None))[1] is None)
    L.append(
        _md_table(
            [
                ("判定类结果", d["n_pass"], d["n_fail"], f"通过率 {rate}"),
                ("环境态", n_other, "—", "不计入判定"),
                (
                    "清册/测试点/功能点",
                    len(d["cases"]),
                    "—",
                    f"{len(d['tps'])} TP / {d['fps_total']} FP",
                ),
            ],
            ["维度", "通过", "未通过", "说明"],
        )
    )
    L.append("\n### 分模块\n")
    L.append(
        _md_table(
            [
                (
                    m,
                    v["pass"],
                    v["fail"],
                    f"{(v['pass'] / (v['pass'] + v['fail']) * 100 if v['pass'] + v['fail'] else 0):.0f}%",
                )
                for m, v in d["by_module"].items()
            ],
            ["模块", "通过", "未通过", "通过率"],
        )
    )
    L.append("\n### 按类型\n")
    L.append(
        _md_table(
            [
                (
                    t,
                    v["pass"],
                    v["fail"],
                    f"{(v['pass'] / (v['pass'] + v['fail']) * 100 if v['pass'] + v['fail'] else 0):.0f}%",
                )
                for t, v in d["by_type"].items()
            ],
            ["类型", "通过", "未通过", "通过率"],
        )
    )

    L.append("\n## 六、结论与风险\n")
    if d["n_judged"]:
        L.append(f"- 判定类 {d['n_pass']} PASS / {d['n_fail']} FAIL（通过率 {rate}）。")
    else:
        L.append("- 本批次全部为环境态结果，暂无可信动态通过率结论。")
    if sc.get("structural_only"):
        L.append(f"- 风险：仅静态断言 {sc['structural_only']} 条，不代表运行时行为。")
    if sc.get("blocked_auth"):
        L.append(f"- 风险：鉴权阻断 {sc['blocked_auth']} 条，需配置凭据后补跑。")
    if sc.get("blocked_review"):
        L.append(f"- 风险：待审批 {sc['blocked_review']} 条（REVIEW_GATE）。")
    if not d["shots"]:
        L.append("- 风险：无执行截图，证据链待补。")

    L.append("\n## 七、监控记录\n")
    L.append(
        _md_table(
            [
                (
                    m["batch_id"],
                    m["state"],
                    m["started_at"],
                    m["finished_at"] or "—",
                    f"{m['done']}/{m['total']}",
                )
                for m in d["monitor"]
            ],
            ["批次", "状态", "开始", "结束", "进度"],
        )
    )

    L.append(f"\n## 八、执行过程截图（{len(d['shots'])} 张）\n")
    if d["shots"]:
        for s in d["shots"][:60]:
            L.append(f"- **{s['id']}** {s['label']}（HTML 版已内嵌原图）")
    else:
        L.append("暂无截图；动态执行后本节列出每条用例的界面证据。\n")

    L.append("\n## 九、最终复用占比\n")
    tt = d["test_type"]
    n_total = sum(v for k, v in tt.items() if k != "(未标记)")
    n_new = tt.get("新增", 0)
    n_reuse = max(n_total - n_new, 0)
    rate_r = f"{n_reuse / n_total * 100:.1f}%" if n_total else "—"
    L.append(
        _md_table(
            [("用例资产（对账后）", n_reuse, n_new, rate_r)],
            ["范围", "复用（沿用+更新）", "新增", "复用占比"],
        )
    )
    lc = d["lifecycle"]
    L.append(
        f"\n> 生命周期：generated×{lc.get('generated', 0)} / updated×{lc.get('updated', 0)} / "
        f"obsolete×{lc.get('obsolete', 0)}；obsolete 不进入执行与导出。\n"
    )

    return "\n".join(L)


# ---------------------------------------------------------------- 6.4 交付
def generate(pid: int, batch_id: str | None = None, out_dir: str | Path | None = None) -> dict:
    """聚合→渲染→落盘 VERIFICATION_REPORT.md/.html，返回路径与汇总。"""
    d = aggregate(pid, batch_id=batch_id)
    out = (
        Path(out_dir)
        if out_dir
        else (
            settings.REPORTS_DIR
            if hasattr(settings, "REPORTS_DIR")
            else Path(__file__).resolve().parents[2] / "data" / "reports"
        )
    )
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / "VERIFICATION_REPORT.md"
    html_path = out / "VERIFICATION_REPORT.html"
    md_path.write_text(render_md(d), encoding="utf-8")
    html_path.write_text(render_html(d), encoding="utf-8")
    return {
        "ok": True,
        "md_path": str(md_path),
        "html_path": str(html_path),
        "batch_id": d["batch"]["batch_id"] if d["batch"] else None,
        "cases": len(d["cases"]),
        "test_points": len(d["tps"]),
        "fps": d["fps_total"],
        "runs": len(d["runs"]),
        "pass": d["n_pass"],
        "fail": d["n_fail"],
        "shots": len(d["shots"]),
    }


full_reporter = None  # 模块级单例不需要；函数即接口
