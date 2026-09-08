"""HTML 报告渲染：把程序生成的测试/验证文档渲染为 test_report.html 模板。

用法：
    from backend.modules.html_report import render_report, from_live_json
    html = render_report(context)                 # context 覆盖默认占位
    html = from_live_json("live_test_results.json")  # 直接吃验证产物 JSON

设计：模板使用 {{token}} 占位；本模块用字符串 replace 逐个替换（避开 str.format
对 CSS 大括号的转义问题）。未提供的 token 自动回退到示例数据，保证模板单独
打开 / 未传参时也是一份“完整可预览”的报告。
"""
from __future__ import annotations
import json
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[2] / "report_templates" / "test_report.html"

# ----------------------------- 示例兜底数据 -----------------------------
SAMPLE = {
    "report_title": "验证报告 · 示例（占位）",
    "report_subtitle": "本报告由 test-accel 自动生成 · 以下为占位示例内容",
    "project_name": "示例项目（请替换为实际项目名）",
    "branch_base": "test-20260906",
    "branch_target": "test-20260907",
    "env_url": "http://47.97.154.50:8090/chat",
    "account": "test_ft001@ft.cntaiping.com",
    "generated_at": "2026-09-07 18:00:00",
    "author": "test-accel / WorkBuddy",
    "kpi_total": "6", "kpi_pass": "5", "kpi_fail": "1", "kpi_rate": "83.3%",
    "change_summary_stat": "对比基准 → 目标：64 个文件变更 / 54 提交 / +2896 -723（占位示例）。",
    "change_summary_body": """
      <tr><td>backend/.../tools/router.py</td><td>新增 195 行</td><td>+195 / -0</td><td>@mention 路由、未知体熔断</td></tr>
      <tr><td>backend/.../tools/toolcall_sanitize.py</td><td>增强 +228 行</td><td>+228 / -12</td><td>参数清洗、超长/特殊字符边界</td></tr>
      <tr><td>backend/.../tests/test_fm007.py</td><td>新增 157 行</td><td>+157 / -0</td><td>FM-007 历史消息重建</td></tr>""",
    "test_points_body": """
      <tr><td>TP-1</td><td>引用不存在的智能体 → 优雅熔断，不挂起</td><td>异常/熔断</td><td>router.py</td><td>线上 T-B</td></tr>
      <tr><td>TP-2</td><td>高频重复工具调用 → 正常终止，不挂起</td><td>正常/长任务</td><td>toolcall_sanitize.py</td><td>线上 T-C</td></tr>
      <tr><td>TP-3</td><td>超长文报告 → 不被截断、完整产出</td><td>边界/输出质量</td><td>toolcall_sanitize.py</td><td>线上 T-D</td></tr>""",
    "cases_body": """
      <tr><td>T-B</td><td>@mention 熔断</td><td>90.2s</td><td>599</td><td><span class="badge pass">PASS</span></td><td>优雅熔断“不存在该智能体”</td></tr>
      <tr><td>T-C</td><td>工具调用终止</td><td>90.2s</td><td>309</td><td><span class="badge pass">PASS</span></td><td>5 次抽样完成并收尾</td></tr>
      <tr><td>T-D</td><td>长文报告不截断</td><td>280.6s</td><td>683</td><td><span class="badge fail">FAIL</span></td><td>超 280s 仍在流式生成</td></tr>""",
    "stats_by_type_body": """
      <tr><td>后端单元测试</td><td>84</td><td>6</td><td>93.3%</td><td>6 项缺运行时数据</td></tr>
      <tr><td>线上场景验证</td><td>5</td><td>1</td><td>83.3%</td><td>T-D 未通过</td></tr>""",
    "conclusions_body": """
      <li>代码变更未引入回归，后端断言级用例全通过。</li>
      <li>熔断 / 护栏 / 历史重建 / 长输入健壮性均符合预期。</li>
      <li>唯一未通过项缺乏“产品缺陷”证据，判定为测试观测超时。</li>""",
    "risks_body": """
      <li>T-D 超长报告未被完整验证（中）。</li>
      <li>6 项单测因缺运行时数据失败（低，CI 注入数据后可转绿）。</li>
      <li>移动端大改未覆盖（中，建议补 UI 回归）。</li>""",
    "reuse_ratio": "82%", "new_ratio": "18%",
    "reuse_detail": "按生效代码量估算：复用约 80–85%，新建/修正约 15–20%（4 处 harness 修正 + 1 诊断脚本，无重写）。",
}


def render_report(context: dict | None = None) -> str:
    """用 context 覆盖 SAMPLE 中的占位，返回完整 HTML 字符串。"""
    tpl = TEMPLATE.read_text(encoding="utf-8")
    data = dict(SAMPLE)
    if context:
        data.update({k: v for k, v in context.items() if v is not None})
    for key, val in data.items():
        tpl = tpl.replace("{{%s}}" % key, str(val))
    return tpl


def from_live_json(json_path: str, meta: dict | None = None) -> str:
    """直接消费验证产物 live_test_results.json，渲染为 HTML。"""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    results = data.get("results", [])
    rows = []
    for r in results:
        ok = bool(r.get("pass_"))
        reasons = "；".join(r.get("reasons", []) or []) or "—"
        rows.append(
            f"<tr><td>{r.get('id','')}</td><td>{r.get('name','')}</td>"
            f"<td>{r.get('elapsed','')}s</td><td>{r.get('resp_len','')}</td>"
            f"<td><span class='badge {'pass' if ok else 'fail'}'>"
            f"{'PASS' if ok else 'FAIL'}</span></td><td>{reasons}</td></tr>")
    total = len(results)
    passed = sum(1 for r in results if r.get("pass_"))
    failed = total - passed
    rate = f"{passed/total*100:.1f}%" if total else "—"
    ctx = {
        "report_title": "验证报告 · 线上环境",
        "report_subtitle": f"验证产物来源：{Path(json_path).name}",
        "project_name": data.get("account", "") or "—",
        "env_url": data.get("env", ""),
        "account": data.get("account", ""),
        "generated_at": data.get("generated_at", ""),
        "author": "test-accel / WorkBuddy",
        "kpi_total": total, "kpi_pass": passed, "kpi_fail": failed, "kpi_rate": rate,
        "cases_body": "\n".join(rows),
        "stats_by_type_body": (
            f"<tr><td>线上场景验证</td><td>{passed}</td><td>{failed}</td>"
            f"<td>{rate}</td><td>来自 {Path(json_path).name}</td></tr>"),
    }
    if meta:
        ctx.update(meta)
    return render_report(ctx)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "report_templates" / "sample_report.html"
    out.write_text(render_report(), encoding="utf-8")
    print("written sample ->", out)
