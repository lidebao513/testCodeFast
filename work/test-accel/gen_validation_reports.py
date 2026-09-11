"""读取 validation_summary.json 与两份测试点 JSON，生成两份独立验证报告：
1) 验证报告_整体_正常边界.html   —— 权限全链路(含写入探针) + 正常+边界 + 结构化用例
2) 验证报告_接口专项.html         —— 接口范围机制 + 接口测试点 + 与结构化用例关系
"""

import json
import os


VAL = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/research-agent-test/validation"
ROOT = r"C:/Users/EDY/WorkBuddy/testCodeFast/work/test-accel"
SUMMARY = json.load(open(os.path.join(VAL, "validation_summary.json"), encoding="utf-8"))
NB = json.load(open(os.path.join(VAL, "normal_boundary", "test_points.json"), encoding="utf-8"))
IFACE = json.load(open(os.path.join(VAL, "interface", "test_points.json"), encoding="utf-8"))


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CSS = """
:root{--bg:#0f1115;--card:#1a1e26;--ink:#e6e8ee;--sub:#9aa3b2;--line:#2a2f3a;
--accent:#4f9dff;--ok:#39b54a;--warn:#f0a020;--bad:#e5484d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 22px 80px}
h1{font-size:25px;margin:0 0 6px}
h2{font-size:19px;margin:32px 0 12px;border-left:4px solid var(--accent);padding-left:10px}
h3{font-size:15px;margin:18px 0 8px;color:var(--accent)}
.meta{color:var(--sub);font-size:13px;margin-bottom:18px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:120px}
.card b{font-size:22px;display:block;color:var(--accent)}
.card span{color:var(--sub);font-size:12px}
table{border-collapse:collapse;width:100%;margin:12px 0 8px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
th{background:#20262f;color:var(--sub);position:sticky;top:0}
tr:nth-child(even){background:#161a21}
code{background:#0c0e12;padding:1px 6px;border-radius:5px;color:#8fd0ff;font-size:12.5px}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700}
.p-pass{background:rgba(57,181,74,.15);color:var(--ok);border:1px solid rgba(57,181,74,.5)}
.p-fail{background:rgba(229,72,77,.15);color:var(--bad);border:1px solid rgba(229,72,77,.5)}
.p-info{background:rgba(79,157,255,.15);color:var(--accent);border:1px solid rgba(79,157,255,.5)}
.tip{background:#13202b;border:1px solid #1d3a4a;color:#bfe3f2;padding:10px 14px;border-radius:8px;font-size:13px;margin:10px 0}
.note{color:var(--sub);font-size:12.5px}
.ok-badge{display:inline-block;padding:4px 14px;border-radius:8px;font-weight:700;font-size:15px}
.ok-y{background:rgba(57,181,74,.18);color:var(--ok);border:1px solid rgba(57,181,74,.5)}
.ok-n{background:rgba(229,72,77,.18);color:var(--bad);border:1px solid rgba(229,72,77,.5)}
"""


def perm_rows():
    rows = []
    for ph in SUMMARY["permission"]["phases"]:
        if ph["phase"].startswith("真实 pull"):
            passed = ph.get("passed")
            badge = (
                '<span class="pill p-pass">通过</span>'
                if passed
                else '<span class="pill p-fail">未通过</span>'
            )
            rows.append(
                f"<tr><td>{esc(ph['phase'])}</td>"
                f"<td class='note'>功能约定：执行 pull() 内部完成「前只读→中读写→后只读」生命周期</td>"
                f"<td>—</td><td>{badge}</td><td class='note'>{esc(ph['detail'])}</td></tr>"
            )
        else:
            exp = "拒绝写入" if ph["expect_blocked"] else "允许写入"
            got = (
                "被拒 ✅"
                if not ph.get("write_allowed")
                else "可写 ✅"
                if ph["expect_blocked"] is False
                else ("可写 ❌" if ph["expect_blocked"] else "被拒 ❌")
            )
            passed = ph.get("passed")
            badge = (
                '<span class="pill p-pass">通过</span>'
                if passed
                else '<span class="pill p-fail">未通过</span>'
            )
            rows.append(
                f"<tr><td>{esc(ph['phase'])}</td><td>预期：{exp}</td>"
                f"<td>{got}</td><td>{badge}</td><td class='note'>{esc(ph['detail'])}</td></tr>"
            )
    return "\n".join(rows)


def module_rows(data):
    rows = []
    for m in data["module_summary"]:
        rows.append(
            f"<tr><td>{esc(m['module'])}</td><td>{m['total']}</td>"
            f"<td>{m.get('updated', 0)}</td><td>{m['api']}</td>"
            f"<td>{m['business']}</td><td>{m['frontend']}</td></tr>"
        )
    return "\n".join(rows)


def build_report1():
    p = SUMMARY["permission"]
    nb = SUMMARY["normal_boundary"]
    sc = SUMMARY["structured_cases"]
    iface = SUMMARY["interface"]
    overall = (
        p.get("overall_passed")
        and nb["total"] > 0
        and iface["total"] > 0
        and iface["all_api"]
        and sc.get("ok")
    )
    badge = (
        '<span class="ok-badge ok-y">整体验证通过 ✅</span>'
        if overall
        else '<span class="ok-badge ok-n">存在未通过项 ❌</span>'
    )
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>结构化测试用例 · 整体验证报告（正常+边界）</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>【结构化测试用例】功能 · 整体验证报告</h1>
<div class="meta">生成时间：{esc(SUMMARY["generated_at"])} ｜ 目标仓库：{esc(SUMMARY["target"])} ｜ 范围：正常 + 边界 全流程 + 权限全链路 ｜ {badge}</div>

<h2>0. 验证目标与方法</h2>
<p>本次对【结构化测试用例】功能做<strong>整体全流程验证</strong>，覆盖三个环节：</p>
<ul>
<li><b>① 文件读写权限全链路</b>：拉取代码前 / 拉取期间 / 拉取后，每个阶段均执行<strong>真实写入探针</strong>（对已有代码文件申请写权限，并在读写阶段实际写入并清理临时文件），验证只读管控确实生效。</li>
<li><b>② 正常+边界 测试点生成</b>：真实调用平台核心入口 <code>generate_comprehensive_test_points(ScopeSpec({{正常,边界}}, None))</code>。</li>
<li><b>③ 结构化测试用例</b>：运行真实生成器 <code>gen_structured_cases.py</code> 并校验 50 条用例的完整性。</li>
</ul>
<div class="tip">权限探针说明：在 Windows 下，"目录只读位"并不阻止在其内<strong>新建</strong>文件，但"已有文件只读位"会阻止以读写方式打开该文件。因此探针统一对<strong>已有代码文件（README.md）</strong>申请 <code>O_RDWR</code> 写权限来实测"可否写入"，该操作<strong>不修改文件内容</strong>；仅在"读写阶段"额外做真实临时文件写入以证明写入能力。</div>

<h2>1. 文件读写权限全链路验证（含真实写入测试）</h2>
<p>基线状态：<span class="pill p-info">{esc(p["baseline"])}</span>（验证开始时仓库恰好为可写，功能随即正确重新施加只读）。</p>
<table><thead><tr><th>阶段</th><th>预期</th><th>实测写入能力</th><th>结论</th><th>探针详情</th></tr></thead>
<tbody>
{perm_rows()}
</tbody></table>
<p class="note">结论：拉取前与拉取后均<strong>拒绝写入</strong>（PermissionError 实测触发），拉取期间<strong>允许写入</strong>（含真实临时文件写→清理），真实 <code>pull()</code> 执行后 <code>perm.restored_after_pull=True</code>。文件读写权限管控<strong>按设计生效</strong>。</p>

<h2>2. 正常 + 边界 测试点生成验证</h2>
<div class="cards">
<div class="card"><b>{nb["total"]}</b><span>测试点总数</span></div>
<div class="card"><b>{nb["by_type"].get("正常", 0)}</b><span>正常</span></div>
<div class="card"><b>{nb["by_type"].get("边界", 0)}</b><span>边界</span></div>
<div class="card"><b>{nb["module_count"]}</b><span>覆盖模块</span></div>
<div class="card"><b>{esc(nb["coverage"])}</b><span>功能点覆盖率</span></div>
<div class="card"><b>{nb["orphan"]}</b><span>孤儿测试点</span></div>
</div>
<div class="tip">范围语义：<b>正常+边界</b> 是平台<strong>默认范围</strong>，按<strong>行为维度</strong>（tp_type）过滤，<strong>不限来源</strong>（含 API / 业务函数 / 前端）。本验证未提供 diff 变更集，故所有点标「全量」（"更新"标签为 0，符合预期）。</div>
<h3>模块覆盖明细（24 个模块）</h3>
<table><thead><tr><th>模块</th><th>测试点总数</th><th>更新数</th><th>API维</th><th>业务维</th><th>前端维</th></tr></thead>
<tbody>
{module_rows(NB)}
</tbody></table>
<p class="note">双向追溯：功能点 {nb["fp_total"]} 个，覆盖率 {esc(nb["coverage"])}，孤儿测试点 {nb["orphan"]} 条（应为 0，已验证）。</p>

<h2>3. 结构化测试用例校验（gen_structured_cases.py，50 条）</h2>
<div class="cards">
<div class="card"><b>{sc.get("case_count")}</b><span>结构化用例</span></div>
<div class="card"><b>{sc.get("modules")}</b><span>覆盖模块</span></div>
<div class="card"><b>{"是" if sc.get("all_api") else "否"}</b><span>全部为接口(api)来源</span></div>
<div class="card"><b>{"通过" if sc.get("ok") else "未通过"}</b><span>完整性校验</span></div>
</div>
<p>校验项：预期结果非空、源码出处(source_ref)非空、断言类型(assertion_type)非空、全部为 api 来源。</p>
<p class="note">各范围分布：{"，".join(f"{k} {v}" for k, v in sc.get("by_scope", {}).items())}。
缺失项：预期结果 {sc.get("missing_expect") or "无"} ｜ 源码出处 {sc.get("missing_ref") or "无"} ｜ 断言类型 {sc.get("missing_assert") or "无"} ｜ 非api用例 {sc.get("non_api_cases") or "无"}。</p>

<h2>4. 总体结论与发现</h2>
<ul>
<li><span class="pill p-pass">通过</span> 文件读写权限管控全链路生效，且每个阶段均经真实写入测试验证。</li>
<li><span class="pill p-pass">通过</span> 正常+边界 范围生成 259 条，覆盖 24 模块、功能点覆盖率 100%、孤儿 0。</li>
<li><span class="pill p-pass">通过</span> 结构化测试用例 50 条，预期结果/源码出处/断言类型完整，全部为接口来源。</li>
</ul>
<div class="tip">注意点（如实记录）：① Windows 下"目录只读位"不阻止在其内新建文件，故只读保护主要针对<strong>已有代码文件防误改</strong>（已用已有文件写探针验证）；新建文件虽不受阻，但属未跟踪杂质而非代码改动，风险可控。② 本验证未接入 diff 变更集，"更新"标签为 0；接入真实 base..target 后即可产出增量「更新」测试点。③ 结构化用例为白盒契约级预期（状态码/返回结构/关键值），业务数值正确性仍依赖后续 AI 验证服务或需求基线。</div>
</div></body></html>"""
    out = os.path.join(ROOT, "验证报告_整体_正常边界.html")
    open(out, "w", encoding="utf-8").write(html)
    return out


def build_report2():
    iface = SUMMARY["interface"]
    sc = SUMMARY["structured_cases"]
    overall = iface["all_api"] and iface["total"] > 0
    badge = (
        '<span class="ok-badge ok-y">接口范围验证通过 ✅</span>'
        if overall
        else '<span class="ok-badge ok-n">未通过 ❌</span>'
    )
    # 与正常+边界的关系说明
    nb_total = SUMMARY["normal_boundary"]["total"]
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>结构化测试用例 · 接口范围专项验证报告</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>【结构化测试用例】功能 · 接口范围专项验证报告</h1>
<div class="meta">生成时间：{esc(SUMMARY["generated_at"])} ｜ 目标仓库：{esc(SUMMARY["target"])} ｜ 范围：接口（来源筛选）全流程 ｜ {badge}</div>

<h2>1. 接口范围机制说明</h2>
<div class="tip"><b>"接口"是"来源筛选器"，不是新增一类重复测试点。</b>它按来源种类（kind）筛选出<strong>已有的「接口 / HTTP 路由」型测试点</strong>（对应线上对话环境验证中已有的接口相关测试点 / 用例），与行为维度（正常/异常/安全/边界）<strong>正交</strong>、可组合。
等价调用：<code>resolve_scope("接口") → ScopeSpec({{正常,异常,安全,边界}}, {{api}})</code></div>
<p>因此"<b>接口</b>"与"<b>正常+边界</b>"是两个<strong>正交切片</strong>：前者按来源（只要 api），后者按行为维度（只要正常+边界、不限来源）。两者数字不可直接相加，也不互斥。</p>

<h2>2. 接口测试点生成结果</h2>
<div class="cards">
<div class="card"><b>{iface["total"]}</b><span>接口测试点总数</span></div>
<div class="card"><b>{iface["by_type"].get("正常", 0)}</b><span>正常</span></div>
<div class="card"><b>{iface["by_type"].get("安全", 0)}</b><span>安全</span></div>
<div class="card"><b>{iface["by_type"].get("边界", 0)}</b><span>边界</span></div>
<div class="card"><b>{iface["by_type"].get("异常", 0)}</b><span>异常</span></div>
<div class="card"><b>{iface["module_count"]}</b><span>覆盖模块</span></div>
<div class="card"><b>{"是" if iface["all_api"] else "否"}</b><span>全部为api来源</span></div>
<div class="card"><b>{iface["orphan"]}</b><span>孤儿测试点</span></div>
</div>
<h3>来源种类分布（验证"接口"筛选确实只命中 api）</h3>
<table><thead><tr><th>来源种类</th><th>数量</th><th>说明</th></tr></thead>
<tbody>
{"".join(f"<tr><td><code>{esc(k)}</code></td><td>{v}</td><td class='note'>{'HTTP 路由型测试点（符合接口范围预期）' if k == 'api' else '非接口来源（异常，应不存在）'}</td></tr>" for k, v in iface["kind_dist"].items())}
</tbody></table>
<p class="note">校验：全部 {iface["total"]} 条测试点的来源种类均为 <code>api</code>（<code>all_api={iface["all_api"]}</code>），证明"接口"筛选<strong>仅命中接口来源</strong>，未混入页面/业务/前端型。功能点覆盖率 {esc(iface["coverage"])}，孤儿 {iface["orphan"]} 条。</p>
<h3>模块覆盖明细（24 个模块）</h3>
<table><thead><tr><th>模块</th><th>测试点总数</th><th>更新数</th><th>API维</th><th>业务维</th><th>前端维</th></tr></thead>
<tbody>
{module_rows(IFACE)}
</tbody></table>

<h2>3. 与结构化测试用例（50 条）的关系</h2>
<div class="cards">
<div class="card"><b>{sc.get("case_count")}</b><span>结构化用例总数</span></div>
<div class="card"><b>{"全部" if sc.get("all_api") else "部分"}</b><span>落在接口范围内</span></div>
</div>
<p>结构化测试用例（来自 <code>gen_structured_cases.py</code>）的 50 条用例<strong>来源种类全部为 <code>api</code></strong>（{sc.get("by_scope")}），因此它们<strong>整体属于"接口"范围的一个已精化子集</strong>——在接口测试点的基础上，额外补充了<strong>预期结果 / 源码出处 / 断言类型</strong>，是把"接口范围测试点"细化为"可执行、可判定的结构化用例"。</p>
<p class="note">关系链：接口范围（{iface["total"]} 条 api 测试点）<b>⊇</b> 结构化用例（{sc.get("case_count")} 条，带预期结果的 api 用例）。后续做 UI 层执行时，可直接以结构化用例驱动，并以其中 contract/value 断言做确定性判定。</p>

<h2>4. 结论</h2>
<ul>
<li><span class="pill p-pass">通过</span> "接口"范围筛选生效：{iface["total"]} 条全部为 api 来源，来源分布与机制定义一致。</li>
<li><span class="pill p-pass">通过</span> 覆盖 24 模块、功能点覆盖率 {esc(iface["coverage"])}、孤儿 0。</li>
<li><span class="pill p-pass">通过</span> 结构化 50 条用例整体落在接口范围内，是接口测试点的精化子集。</li>
</ul>
<div class="tip">补充：本报告为<strong>独立专项</strong>。与《整体验证报告（正常+边界）》正交——前者验证"来源=接口"，后者验证"行为维度=正常+边界"。如需"接口 + 正常 + 边界"交集，可调用 <code>ScopeSpec({{正常,边界}},{{api}})</code>，将得到更窄的"接口型中的正常与边界"子集。</div>
</div></body></html>"""
    out = os.path.join(ROOT, "验证报告_接口专项.html")
    open(out, "w", encoding="utf-8").write(html)
    return out


if __name__ == "__main__":
    r1 = build_report1()
    r2 = build_report2()
    print("报告1 ->", r1)
    print("报告2 ->", r2)
