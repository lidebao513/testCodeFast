"""阶段6 批次2（P6-②1 趋势/flaky + P6-②2 覆盖率报告）。

纯分析模块（只读 DB，不改写任何数据），对外提供：
- trend(pid)       多批次执行趋势（基于 run_batches 持久化批次序列）
- flaky(pid)       跨批次结果不一致的用例（flaky / 不稳定识别）
- coverage(pid)    用例 vs 测试点 vs 功能点 覆盖率，定位未覆盖缺口
- render_trend_coverage_html(pid)  把三者拼成一份可视化 HTML 报告

取数来源：
- 趋势：run_batches（每次 run_project 必落库，覆盖 scan_and_test / execute）
- flaky：runs（case_id + batch_id + status）
- 覆盖率：functional_points / test_points / cases 三表关联
"""

import json
from collections import Counter, defaultdict

from backend.core.enums import (
    ExecStatus,
)
from backend.db import get_conn


# ---------------------------------------------------------------------------
# 趋势（P6-②1）
# ---------------------------------------------------------------------------


def _pass_rate(sc):
    """从状态计数 dict 计算真实通过率：pass / (pass + fail)。"""
    p, f = sc.get(ExecStatus.PASS.value, 0), sc.get(ExecStatus.FAIL.value, 0)
    eff = p + f
    return round(100.0 * p / eff, 1) if eff else None


def trend(pid, only_finished=True):
    """多批次执行趋势序列。

    返回 points（按 started_at 升序），每个点含：
      batch_id / started_at / state / total / pass / fail /
      effective_total / pass_rate / structural_only / blocked_auth / error
    only_finished=False 时连 running 批次也纳入（一般只看已结束的）。
    """
    conn = get_conn()
    cur = conn.cursor()
    if only_finished:
        cur.execute(
            "SELECT batch_id, state, started_at, status_counts FROM run_batches "
            "WHERE project_id=? AND state!='running' ORDER BY started_at ASC",
            (pid,),
        )
    else:
        cur.execute(
            "SELECT batch_id, state, started_at, status_counts FROM run_batches "
            "WHERE project_id=? ORDER BY started_at ASC",
            (pid,),
        )
    rows = cur.fetchall()
    conn.close()

    points = []
    for row in rows:
        try:
            sc = json.loads(row["status_counts"] or "{}")
        except Exception:
            sc = {}
        total = sum(sc.values())
        pr = _pass_rate(sc)
        points.append(
            {
                "batch_id": row["batch_id"],
                "started_at": row["started_at"],
                "state": row["state"],
                "total": total,
                ExecStatus.PASS.value: sc.get(ExecStatus.PASS.value, 0),
                ExecStatus.FAIL.value: sc.get(ExecStatus.FAIL.value, 0),
                "effective_total": sc.get(ExecStatus.PASS.value, 0)
                + sc.get(ExecStatus.FAIL.value, 0),
                "pass_rate": pr,
                ExecStatus.STRUCTURAL_ONLY.value: sc.get(ExecStatus.STRUCTURAL_ONLY.value, 0),
                ExecStatus.BLOCKED_AUTH.value: sc.get(ExecStatus.BLOCKED_AUTH.value, 0),
                ExecStatus.ERROR.value: sc.get(ExecStatus.ERROR.value, 0),
            }
        )
    # 趋势方向（最后两次有效 pass_rate 比较）
    rates = [(p["started_at"], p["pass_rate"]) for p in points if p["pass_rate"] is not None]
    direction = "stable"
    if len(rates) >= 2:
        if rates[-1][1] > rates[-2][1]:
            direction = "improving"
        elif rates[-1][1] < rates[-2][1]:
            direction = "regressing"
    return {
        "ok": True,
        "count": len(points),
        "pass_rate_direction": direction,
        "points": points,
    }


# ---------------------------------------------------------------------------
# Flaky 识别（P6-②1）
# ---------------------------------------------------------------------------

# 真正"有结论"的状态——用于判断不稳定（环境态不计入）
_VERDICT_STATUSES = (ExecStatus.PASS.value, ExecStatus.FAIL.value, ExecStatus.ERROR.value)


def flaky(pid, min_batches=2):
    """跨批次结果不一致的用例（flaky 识别）。

    基于 runs 表 (case_id, batch_id, status)。一个用例若在 >= min_batches 个
    不同批次中执行，且"结论状态"集合不一致（同时出现 pass 与非 pass 结论），
    视为不稳定（flaky）。structural_only / blocked_auth 属环境态，单独记录但不
    直接计入"不稳定"。
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT case_id, batch_id, status FROM runs "
        "WHERE project_id=? AND case_id IS NOT NULL AND batch_id IS NOT NULL "
        "ORDER BY id",
        (pid,),
    )
    rows = cur.fetchall()
    conn.close()

    by_case = defaultdict(list)
    for r in rows:
        by_case[r["case_id"]].append((r["batch_id"], r["status"]))

    cohorts = []
    for cid, recs in by_case.items():
        batches = {b for b, _ in recs}
        if len(batches) < min_batches:
            continue
        statuses = [s for _, s in recs]
        verdicts = [s for s in statuses if s in _VERDICT_STATUSES]
        distinct = set(verdicts)
        is_flaky = (
            len(distinct) > 1
            and ExecStatus.PASS.value in distinct
            and (ExecStatus.FAIL.value in distinct or ExecStatus.ERROR.value in distinct)
        )
        by_batch = {}
        for b, s in recs:  # 同一批次内取最后一次状态
            by_batch[b] = s
        cohorts.append(
            {
                "case_id": cid,
                "batches": len(batches),
                "executions": len(recs),
                "statuses": statuses,
                "by_batch": by_batch,
                "flaky": is_flaky,
                "distinct_verdicts": sorted(distinct),
            }
        )

    flaky_cases = sorted(
        [c for c in cohorts if c["flaky"]],
        key=lambda c: (c["batches"], c["executions"]),
        reverse=True,
    )
    # 不一致但非经典 flaky（如 structural_only<->blocked_auth 变化，无 pass 对照）
    inconsistent = sorted(
        [c for c in cohorts if not c["flaky"] and len(set(c["statuses"])) > 1],
        key=lambda c: c["batches"],
        reverse=True,
    )

    return {
        "ok": True,
        "min_batches": min_batches,
        "cases_seen": len(by_case),
        "evaluated": len(cohorts),
        "flaky_count": len(flaky_cases),
        "flaky": flaky_cases,
        "inconsistent_nonflaky": inconsistent,
    }


# ---------------------------------------------------------------------------
# 覆盖率（P6-②2）
# ---------------------------------------------------------------------------


def coverage(pid):
    """用例 vs 测试点 vs 功能点 覆盖率，定位未覆盖缺口。

    覆盖链路：功能点(FP) --(fp_contract_id)--> 测试点(TP) --(tp_id)--> 用例(Case)
    - FP 覆盖率：有 >=1 个 TP 指回的 FP 占比（功能点零测试点 = 缺口）
    - TP 覆盖率：有 >=1 个有效用例的 TP 占比（测试点零用例 = 缺口）
    - 模块级：按 module 拆分三类覆盖率
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, contract_id, name, module, ftype FROM functional_points WHERE project_id=?",
        (pid,),
    )
    fps = [dict(r) for r in cur.fetchall()]

    cur.execute(
        "SELECT tp_id, fp_contract_id, module, title FROM test_points WHERE project_id=?", (pid,)
    )
    tps = [dict(r) for r in cur.fetchall()]

    # 有效用例（排除 obsolete / archived；其余生命周期状态均视为"在用"）
    cur.execute(
        "SELECT id, tp_id, fp_contract_id, module, title, status FROM cases "
        "WHERE project_id=? AND COALESCE(status,'') NOT IN ('obsolete','archived')",
        (pid,),
    )
    cases = [dict(r) for r in cur.fetchall()]
    conn.close()

    fp_by_cid = {fp["contract_id"]: fp for fp in fps}
    tp_by_id = {tp["tp_id"]: tp for tp in tps}

    fp_with_tp = {tp["fp_contract_id"] for tp in tps if tp["fp_contract_id"]}
    tp_with_case = {c["tp_id"] for c in cases if c["tp_id"]}

    fp_total = len(fps)
    fp_covered = len(fp_with_tp & set(fp_by_cid.keys()))
    tp_total = len(tps)
    tp_covered = len(tp_with_case & set(tp_by_id.keys()))
    case_active = len(cases)

    uncovered_fps = [
        {
            "contract_id": fp["contract_id"],
            "name": fp["name"],
            "module": fp["module"],
            "ftype": fp["ftype"],
        }
        for fp in fps
        if fp["contract_id"] not in fp_with_tp
    ]
    uncovered_tps = [
        {
            "tp_id": tp["tp_id"],
            "title": tp["title"],
            "module": tp["module"],
            "fp_contract_id": tp["fp_contract_id"],
        }
        for tp in tps
        if tp["tp_id"] not in tp_with_case
    ]

    # 模块级覆盖
    mod_fp = Counter(fp["module"] or "未分类" for fp in fps)
    mod_fp_cov = Counter(fp["module"] or "未分类" for fp in fps if fp["contract_id"] in fp_with_tp)
    mod_tp = Counter(tp["module"] or "未分类" for tp in tps)
    mod_tp_cov = Counter(tp["module"] or "未分类" for tp in tps if tp["tp_id"] in tp_with_case)

    module_coverage = {}
    for m in set(list(mod_fp) + list(mod_tp)):
        fpt, fpc = mod_fp.get(m, 0), mod_fp_cov.get(m, 0)
        tpt, tpc = mod_tp.get(m, 0), mod_tp_cov.get(m, 0)
        module_coverage[m] = {
            "fp_total": fpt,
            "fp_covered": fpc,
            "fp_rate": round(100.0 * fpc / fpt, 1) if fpt else 100.0,
            "tp_total": tpt,
            "tp_covered": tpc,
            "tp_rate": round(100.0 * tpc / tpt, 1) if tpt else 100.0,
        }

    def _rate(a, b):
        return round(100.0 * a / b, 1) if b else 0.0

    return {
        "ok": True,
        "fp_total": fp_total,
        "fp_covered": fp_covered,
        "fp_rate": _rate(fp_covered, fp_total),
        "tp_total": tp_total,
        "tp_covered": tp_covered,
        "tp_rate": _rate(tp_covered, tp_total),
        "case_active": case_active,
        "uncovered_fp_count": len(uncovered_fps),
        "uncovered_tp_count": len(uncovered_tps),
        "uncovered_fps": uncovered_fps,
        "uncovered_tps": uncovered_tps,
        "module_coverage": module_coverage,
    }


# ---------------------------------------------------------------------------
# HTML 报告（趋势 + flaky + 覆盖率 合订）
# ---------------------------------------------------------------------------


def _line_chart(points, key, color, height=160):
    """在 680 宽画布上画一条折线图（key 取值可能为 None，None 点留空）。"""
    if not points:
        return "<div style='color:#888;font-size:12px'>无数据</div>"
    n = len(points)
    w, h = 680, height
    pad_l, pad_r, pad_t, pad_b = 40, 16, 14, 26
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    # y 轴范围：pass_rate 0-100；其它计数取 0..max
    if key == "pass_rate":
        ymax, ymin = 100.0, 0.0
    else:
        vals = [p[key] for p in points if isinstance(p[key], (int, float))]
        ymax = max(vals) if vals else 1
        ymin = 0.0
    ymax = ymax * 1.1 or 1

    def x(i):
        return pad_l + (plot_w * i / max(n - 1, 1))

    def y(v):
        if v is None:
            return None
        return pad_t + plot_h * (1 - (v - ymin) / (ymax - ymin))

    path = []
    for i, p in enumerate(points):
        v = p.get(key)
        yy = y(v)
        if yy is None:
            continue
        path.append(f"{x(i):.1f},{yy:.1f}")
    poly = " ".join(path)
    # y 轴刻度
    ticks = ""
    for t in (0.0, 0.5, 1.0):
        vv = ymin + (ymax - ymin) * t
        yy = pad_t + plot_h * (1 - t)
        ticks += (
            f"<line x1='{pad_l}' y1='{yy:.1f}' x2='{w - pad_r}' y2='{yy:.1f}' "
            f"stroke='#e3e6ea'/>"
            f"<text x='{pad_l - 6}' y='{yy + 3:.1f}' text-anchor='end' "
            f"font-size='10' fill='#888'>{vv:.0f}</text>"
        )
    # x 标签（首/中/尾）
    xlabels = ""
    for i in (0, n // 2, n - 1):
        if 0 <= i < n:
            lbl = points[i]["started_at"][5:16] if points[i].get("started_at") else str(i)
            xlabels += (
                f"<text x='{x(i):.1f}' y='{h - 8}' text-anchor='middle' "
                f"font-size='9' fill='#888'>{lbl}</text>"
            )
    body = (
        f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{poly}'/>" if poly else ""
    )
    dots = ""
    for i, p in enumerate(points):
        v = p.get(key)
        yy = y(v)
        if yy is None:
            continue
        dots += f"<circle cx='{x(i):.1f}' cy='{yy:.1f}' r='3' fill='{color}'/>"
    return (
        f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:680px'>"
        f"{ticks}{body}{dots}{xlabels}</svg>"
    )


def render_trend_coverage_html(pid):
    """把 趋势 / flaky / 覆盖率 三者拼成一份浅色 HTML 报告。"""
    tr = trend(pid)
    fl = flaky(pid)
    cov = coverage(pid)
    pts = tr["points"]

    # KPI 卡片
    kpis = (
        f"<div class='kpi'><div class='n'>{tr['count']}</div>执行批次</div>"
        f"<div class='kpi'><div class='n' style='color:#C2410C'>{fl['flaky_count']}</div>flaky 用例</div>"
        f"<div class='kpi'><div class='n' style='color:#1D9E75'>{cov['fp_rate']}%</div>功能点覆盖</div>"
        f"<div class='kpi'><div class='n' style='color:#1D9E75'>{cov['tp_rate']}%</div>测试点覆盖</div>"
    )

    # 趋势表
    trend_rows = ""
    for p in pts:
        pr = p["pass_rate"]
        pr_s = f"{pr}%" if pr is not None else "—"
        trend_rows += (
            f"<tr><td>{p['started_at']}</td><td><code>{p['batch_id']}</code></td>"
            f"<td>{p['state']}</td><td>{p['total']}</td><td style='color:#1D9E75'>{p[ExecStatus.PASS.value]}</td>"
            f"<td style='color:#E24B4A'>{p[ExecStatus.FAIL.value]}</td><td><b>{pr_s}</b></td>"
            f"<td style='color:#6B7785'>{p[ExecStatus.STRUCTURAL_ONLY.value]}</td>"
            f"<td style='color:#8B5CF6'>{p[ExecStatus.BLOCKED_AUTH.value]}</td>"
            f"<td style='color:#C2410C'>{p[ExecStatus.ERROR.value]}</td></tr>"
        )
    direction_map = {"improving": "📈 改善", "regressing": "📉 退化", "stable": "➖ 平稳"}
    trend_html = (
        f"<h3>执行趋势（{tr['count']} 个批次 · 方向：{direction_map.get(tr['pass_rate_direction'], '')}）</h3>"
        f"<div class='card'>{_line_chart(pts, 'pass_rate', '#1D9E75')}"
        f"<div style='font-size:11px;color:#888'>真实通过率（pass / (pass+fail)）趋势</div></div>"
        f"<div class='card'>{_line_chart(pts, 'total', '#2563eb')}"
        f"<div style='font-size:11px;color:#888'>每批次执行用例总数趋势</div></div>"
        f"<table><tr><th>时间</th><th>批次</th><th>状态</th><th>总数</th><th>通过</th>"
        f"<th>失败</th><th>通过率</th><th>仅静态</th><th>需鉴权</th><th>异常</th></tr>"
        f"{trend_rows}</table>"
    )

    # Flaky 表 + 通俗解析
    flaky_explain = (
        f"<div class='explain'>"
        f"<b>📖 怎么读懂这一栏（给非技术同学）</b><br><br>"
        f"<b>什么是 Flaky 用例？</b> 正常的测试用例每次运行结果都一样（要么一直通过，要么一直失败）；"
        f"而 <b>Flaky（不稳定的）用例</b>就像“时好时坏的灯泡”——代码一行没改，它这次跑过、下次却挂了，结果飘忽不定。<br><br>"
        f"<b>为什么要专门盯它？</b> Flaky 用例会“狼来了”：当它偶尔失败时，团队分不清到底是真有 bug，还是它自己抽风，"
        f"既容易掩盖真正的问题，又浪费大量排查时间。所以平台会自动把每个用例在<b>多次执行批次</b>里的结果拿来比对，"
        f"一旦发现某用例既出现过“通过”又出现过“失败 / 报错”，就把它揪出来列在这。<br><br>"
        f"<b>为什么现在是 0 条？</b> 本次共评估了 <b>{fl['evaluated']}</b> 个“跑过多次”的用例，"
        f"它们在全部 {tr['count']} 个执行批次里的结果<b>完全一致</b>（都稳定通过，或都稳定地因环境限制而跳过 / 未探测），"
        f"没有任何一个用例出现“时过时挂”的摇摆，因此没有发现不稳定用例。<br><br>"
        f"<b>这反映了什么？</b> 这是<b>健康信号</b>：至少在当前数据下，测试结果是可信、可复现的。"
        f"不过也要说明：本报告目前的基础数据以“静态结构检查”为主、真实运行时探测尚未广泛开展，"
        f"所以 0 条也部分源于“还没有触发真实的运行时波动”。等后续接入真实被测服务、跑出真实的通过 / 失败动态结果后，"
        f"若有用例开始“时过时挂”，本栏会自动把它们列出来，方便定位并加固（例如加重试、隔离外部依赖等）。"
        f"</div>"
    )
    if fl["flaky"]:
        fl_rows = ""
        for c in fl["flaky"]:
            byb = "；".join(f"{b[:14]}:{s}" for b, s in c["by_batch"].items())
            fl_rows += (
                f"<tr><td>{c['case_id']}</td><td>{c['batches']}</td>"
                f"<td>{c['executions']}</td><td style='color:#C2410C'><b>flaky</b></td>"
                f"<td>{byb}</td></tr>"
            )
        flaky_html = (
            f"<h3>Flaky 用例（{fl['flaky_count']} 条）</h3>"
            f"<table><tr><th>Case</th><th>批次</th><th>执行次数</th><th>判定</th>"
            f"<th>各批次状态</th></tr>{fl_rows}</table>"
            f"{flaky_explain}"
        )
    else:
        flaky_html = (
            f"<h3>Flaky 用例（0 条）</h3>"
            f"<div class='card' style='color:#1D9E75'>✅ 未检测到跨批次结果不一致的用例"
            f"（已评估 {fl['evaluated']} 个多批次用例）。</div>"
            f"{flaky_explain}"
        )
    if fl["inconsistent_nonflaky"]:
        inc = "；".join(
            f"case {c['case_id']}（{c['batches']} 批，状态 {c['statuses']}）"
            for c in fl["inconsistent_nonflaky"][:10]
        )
        flaky_html += (
            f"<div class='card' style='font-size:12px;color:#BA7517'>"
            f"其它一致性变化（非经典 flaky，多为环境态如 structural_only↔blocked_auth）："
            f"{inc}</div>"
        )

    # 覆盖率
    mod_rows = ""
    for m, d in sorted(
        cov["module_coverage"].items(), key=lambda kv: kv[1]["fp_total"], reverse=True
    ):
        mod_rows += (
            f"<tr><td>{m}</td><td>{d['fp_total']}</td><td>{d['fp_covered']} "
            f"({d['fp_rate']}%)</td><td>{d['tp_total']}</td>"
            f"<td>{d['tp_covered']} ({d['tp_rate']}%)</td></tr>"
        )
    gap_fp = cov["uncovered_fp_count"]
    gap_tp = cov["uncovered_tp_count"]
    gap_html = f"未覆盖功能点 <b>{gap_fp}</b> 个　未覆盖测试点 <b>{gap_tp}</b> 个"
    if gap_fp:
        items = "".join(
            f"<li><code>{f['contract_id']}</code> 【{f['ftype']}】{f['name']} "
            f"（{f['module']}）</li>"
            for f in cov["uncovered_fps"][:50]
        )
        gap_html += f"<details><summary>未覆盖功能点明细</summary><ul>{items}</ul></details>"
    if gap_tp:
        items = "".join(
            f"<li><code>{t['tp_id']}</code> {t['title']}（{t['module']}）</li>"
            for t in cov["uncovered_tps"][:50]
        )
        gap_html += f"<details><summary>未覆盖测试点明细</summary><ul>{items}</ul></details>"

    coverage_html = (
        f"<h3>覆盖率（用例 ↔ 测试点 ↔ 功能点）</h3>"
        f"<div class='card'>{gap_html}</div>"
        f"<table><tr><th>模块</th><th>功能点总数</th><th>功能点覆盖</th>"
        f"<th>测试点总数</th><th>测试点覆盖</th></tr>{mod_rows}</table>"
    )

    gen = __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>趋势与覆盖率报告</title>
<style>
body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:32px;color:#1a1a1a;background:#fff;}}
h1{{font-size:20px;}} h3{{margin-top:28px;border-left:4px solid #2563eb;padding-left:10px;}}
.card{{background:#f6f7f9;border:1px solid #e3e6ea;border-radius:10px;padding:14px;margin:12px 0;}}
.explain{{background:#FFFDF5;border:1px solid #F2E2A8;border-left:4px solid #E0B53D;
border-radius:10px;padding:14px 16px;margin:12px 0;font-size:13px;line-height:1.75;color:#4a4636;}}
.kpis{{display:flex;gap:12px;flex-wrap:wrap;}} .kpi{{flex:1;min-width:110px;text-align:center;
background:#fff;border:1px solid #e3e6ea;border-radius:10px;padding:14px;}}
.kpi .n{{font-size:26px;font-weight:600;}}
table{{width:100%;border-collapse:collapse;margin-top:8px;}}
th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #eee;font-size:12.5px;vertical-align:top;}}
th{{background:#f0f2f5;}} code{{font-size:11px;color:#555;}}
</style></head><body>
<h1>测试加速平台 · 趋势与覆盖率报告</h1>
<div class="card"><b>项目 ID：</b>{pid}　<b>生成时间：</b>{gen}</div>
<div class="kpis">{kpis}</div>
{trend_html}
{flaky_html}
{coverage_html}
</body></html>"""
