"""阶段6 批次3（P6-②3 报告导出 PDF/Word/Excel）。

纯导出模块：把已落库的某份报告（summary + 用例明细 results）渲染为
  - Excel  (.xlsx, openpyxl)
  - Word   (.docx, python-docx)
  - PDF    (.pdf,  reportlab，内置 STSong-Light 中日韩字体保证中文不乱码)
对外不依赖被测服务，只读 reports 表 + 同时间戳 JSON 文件。
"""

import json
from pathlib import Path

from backend.config import settings
from backend.modules.reporter import reporter


# ---------------------------------------------------------------------------
# 公共：取报告数据（summary + results）
# ---------------------------------------------------------------------------
def _load_report(pid, rid):
    detail = reporter.build_report_detail(pid, rid, inline=False)
    if detail is None:
        return None
    html_path = detail.get("html_path")
    results = []
    if html_path:
        jp = Path(html_path).with_suffix(".json")
        if jp.exists():
            try:
                results = json.loads(jp.read_text(encoding="utf-8")).get("results", [])
            except Exception:
                results = []
    return detail, results


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------
def export_excel(pid, rid, out_path, project=""):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    loaded = _load_report(pid, rid)
    if loaded is None:
        return None
    detail, results = loaded
    s = detail.get("summary", {})
    wb = Workbook()
    ws = wb.active
    ws.title = "摘要"
    hdr_fill = PatternFill("solid", fgColor="2563EB")
    hdr_font = Font(bold=True, color="FFFFFF")
    rows = [
        ("项目", project or s.get("project", "")),
        ("生成时间", s.get("generated_at", "")),
        ("批次", s.get("batch_id", "")),
        ("总用例", s.get("total", 0)),
        ("通过", s.get("pass", 0)),
        ("失败", s.get("fail", 0)),
        ("跳过", s.get("skipped", 0)),
        ("仅静态验证", s.get("structural_only", 0)),
        ("需鉴权", s.get("blocked_auth", 0)),
        ("执行异常", s.get("error", 0)),
        ("评审阻塞", s.get("blocked_review", 0)),
        ("有效总数(通过+失败)", s.get("effective_total", 0)),
        ("真实通过率", _rate(s)),
    ]
    for i, (k, v) in enumerate(rows, 1):
        c1 = ws.cell(i, 1, k)
        c1.font = Font(bold=True)
        c2 = ws.cell(i, 2, v)
        if i == 1:
            c1.fill = hdr_fill
            c1.font = hdr_font
            c2.fill = hdr_fill
            c2.font = hdr_font
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 40

    # 失败归因
    fl = s.get("failures", {})
    r0 = len(rows) + 2
    ws.cell(r0, 1, "失败归因（按状态）").font = Font(bold=True)
    for j, (k, v) in enumerate(fl.get("by_status", {}).items(), 1):
        ws.cell(r0 + j, 1, k)
        ws.cell(r0 + j, 2, v)
    r1 = r0 + len(fl.get("by_status", {})) + 2
    ws.cell(r1, 1, "失败聚类（模块×状态）").font = Font(bold=True)
    for j, c in enumerate(fl.get("clusters", [])[:15], 1):
        ws.cell(r1 + j, 1, f"{c['module']} [{c['status']}] {c['count']} 条")
        ws.cell(r1 + j, 2, f"样例 case_id={c['samples']}")

    # 用例明细
    ws2 = wb.create_sheet("用例明细")
    headers = [
        "case_id",
        "module",
        "ctype",
        "status",
        "title",
        "tp_id",
        "fp_contract_id",
        "source",
        "reason",
    ]
    ws2.append(headers)
    for col in range(1, len(headers) + 1):
        cell = ws2.cell(1, col)
        cell.font = hdr_font
        cell.fill = hdr_fill
    for r in results:
        ws2.append(
            [
                r.get("case_id", ""),
                r.get("module") or "",
                r.get("ctype", ""),
                r.get("status", ""),
                (r.get("title") or "")[:80],
                r.get("tp_id") or "",
                r.get("fp_contract_id") or "",
                r.get("source") or "",
                (r.get("reason") or r.get("log") or "")[:300],
            ]
        )
    widths = [10, 16, 8, 14, 40, 14, 16, 30, 60]
    for i, w in enumerate(widths, 1):
        ws2.column_dimensions[chr(64 + i)].width = w
    ws2.freeze_panes = "A2"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------
def export_word(pid, rid, out_path, project=""):
    from docx import Document
    from docx.shared import Pt

    loaded = _load_report(pid, rid)
    if loaded is None:
        return None
    detail, results = loaded
    s = detail.get("summary", {})
    doc = Document()
    doc.add_heading("测试加速平台 · 扫描测试报告", level=0)
    p = doc.add_paragraph()
    p.add_run(
        f"项目：{project or s.get('project', '')}　生成时间：{s.get('generated_at', '')}"
        f"　批次：{s.get('batch_id', '')}"
    )

    doc.add_heading("一、执行摘要", level=1)
    es = s.get("exec_summary") or {}
    if es:
        hp = doc.add_paragraph()
        run = hp.add_run(es.get("headline", ""))
        run.bold = True
        run.font.size = Pt(13)
        for b in es.get("bullets", []):
            doc.add_paragraph(b, style="List Bullet")
    else:
        doc.add_paragraph("（未生成执行摘要）")

    doc.add_heading("二、关键指标", level=1)
    t = doc.add_table(rows=1, cols=2)
    t.style = "Light Grid Accent 1"
    t.rows[0].cells[0].text = "指标"
    t.rows[0].cells[1].text = "值"
    for k, v in [
        ("总用例", s.get("total", 0)),
        ("通过", s.get("pass", 0)),
        ("失败", s.get("fail", 0)),
        ("跳过", s.get("skipped", 0)),
        ("仅静态验证", s.get("structural_only", 0)),
        ("需鉴权", s.get("blocked_auth", 0)),
        ("执行异常", s.get("error", 0)),
        ("评审阻塞", s.get("blocked_review", 0)),
        ("真实通过率", _rate(s)),
    ]:
        row = t.add_row().cells
        row[0].text = str(k)
        row[1].text = str(v)

    doc.add_heading("三、失败归因", level=1)
    fl = s.get("failures", {})
    doc.add_paragraph(
        "按状态：" + ("；".join(f"{k}:{v}" for k, v in fl.get("by_status", {}).items()) or "无")
    )
    for c in fl.get("clusters", [])[:10]:
        doc.add_paragraph(
            f"{c['module']} [{c['status']}] {c['count']} 条　样例 case_id={c['samples']}",
            style="List Bullet",
        )

    doc.add_heading("四、用例明细", level=1)
    t2 = doc.add_table(rows=1, cols=5)
    t2.style = "Light Grid Accent 1"
    for i, h in enumerate(["case_id", "模块", "状态", "标题", "说明"]):
        t2.rows[0].cells[i].text = h
    for r in results:
        cells = t2.add_row().cells
        cells[0].text = str(r.get("case_id", ""))
        cells[1].text = str(r.get("module") or "")
        cells[2].text = str(r.get("status", ""))
        cells[3].text = str((r.get("title") or "")[:50])
        cells[4].text = str((r.get("reason") or r.get("log") or "")[:120])

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# PDF (reportlab + 中日韩字体)
# ---------------------------------------------------------------------------
def _cjk_font():
    """返回可用的中文字体名；优先级：reportlab 内置 STSong-Light → 系统雅黑/宋体 TTF。"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        pass
    for p in [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]:
        if Path(p).exists():
            try:
                from reportlab.pdfbase.ttfonts import TTFont

                pdfmetrics.registerFont(TTFont("CJK", p))
                return "CJK"
            except Exception:
                continue
    return "Helvetica"


def export_pdf(pid, rid, out_path, project=""):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    loaded = _load_report(pid, rid)
    if loaded is None:
        return None
    detail, results = loaded
    s = detail.get("summary", {})
    font = _cjk_font()
    ss = getSampleStyleSheet()
    base = ParagraphStyle("base", parent=ss["Normal"], fontName=font, fontSize=9, leading=12)
    title = ParagraphStyle("title", parent=ss["Title"], fontName=font, fontSize=16)
    ParagraphStyle("h2", parent=ss["Heading2"], fontName=font, fontSize=12)
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName=font, fontSize=13)

    story = [Paragraph("测试加速平台 · 扫描测试报告", title)]
    story.append(
        Paragraph(
            f"项目：{project or s.get('project', '')}　生成时间：{s.get('generated_at', '')}"
            f"　批次：{s.get('batch_id', '')}",
            base,
        )
    )
    story.append(Spacer(1, 4))

    es = s.get("exec_summary") or {}
    if es:
        story.append(Paragraph("一、执行摘要", h1))
        story.append(Paragraph(f"<b>{es.get('headline', '')}</b>", base))
        for b in es.get("bullets", []):
            story.append(Paragraph(f"• {b}", base))
        story.append(Spacer(1, 6))

    story.append(Paragraph("二、关键指标", h1))
    metr = [
        ["指标", "值"],
        ["总用例", s.get("total", 0)],
        ["通过", s.get("pass", 0)],
        ["失败", s.get("fail", 0)],
        ["跳过", s.get("skipped", 0)],
        ["仅静态验证", s.get("structural_only", 0)],
        ["需鉴权", s.get("blocked_auth", 0)],
        ["执行异常", s.get("error", 0)],
        ["评审阻塞", s.get("blocked_review", 0)],
        ["真实通过率", _rate(s)],
    ]
    mt = Table(metr, colWidths=[60 * mm, 90 * mm])
    mt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
            ]
        )
    )
    story.append(mt)

    fl = s.get("failures", {})
    if fl.get("by_status") or fl.get("clusters"):
        story.append(Spacer(1, 6))
        story.append(Paragraph("三、失败归因", h1))
        story.append(
            Paragraph(
                "按状态："
                + ("；".join(f"{k}:{v}" for k, v in fl.get("by_status", {}).items()) or "无"),
                base,
            )
        )
        for c in fl.get("clusters", [])[:10]:
            story.append(
                Paragraph(
                    f"{c['module']} [{c['status']}] {c['count']} 条　样例 case_id={c['samples']}",
                    base,
                )
            )

    story.append(Spacer(1, 6))
    story.append(Paragraph(f"四、用例明细（共 {len(results)} 条）", h1))
    data = [["case_id", "模块", "状态", "标题", "说明"]]
    for r in results:
        data.append(
            [
                str(r.get("case_id", "")),
                str(r.get("module") or ""),
                str(r.get("status", "")),
                str((r.get("title") or "")[:40]),
                str((r.get("reason") or r.get("log") or "")[:80]),
            ]
        )
    rt = Table(data, colWidths=[16 * mm, 26 * mm, 24 * mm, 44 * mm, 60 * mm], repeatRows=1)
    rt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f8fa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(rt)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    ).build(story)
    return out_path


# ---------------------------------------------------------------------------
# 调度
# ---------------------------------------------------------------------------
def _rate(s):
    eff = s.get("effective_total") or (s.get("pass", 0) + s.get("fail", 0))
    if not eff:
        return "—"
    return f"{round(100.0 * s.get('pass', 0) / eff, 1)}%"


def export_report(pid, rid, fmt="xlsx", out_dir=None):
    """导出指定报告为 xlsx / docx / pdf，返回文件路径；格式不支持或报告不存在返回 None。"""
    fmt = (fmt or "xlsx").lower()
    if fmt not in ("xlsx", "docx", "pdf"):
        # 容错别名
        fmt = {"excel": "xlsx", "word": "docx", "pdf": "pdf"}.get(fmt, "xlsx")
    out_dir = Path(out_dir or settings.REPORTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    project = ""
    try:
        d = reporter.build_report_detail(pid, rid, inline=False)
        project = (d or {}).get("summary", {}).get("project", "") if d else ""
    except Exception:
        pass
    path = out_dir / f"report_{pid}_{rid}.{fmt}"
    if fmt == "xlsx":
        return export_excel(pid, rid, path, project)
    if fmt == "docx":
        return export_word(pid, rid, path, project)
    if fmt == "pdf":
        return export_pdf(pid, rid, path, project)
    return None
