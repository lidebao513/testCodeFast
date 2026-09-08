"""报告功能 CLI：把程序生成的文档转成 HTML 报告。

用法：
  # 1) 用验证产物 JSON 直接转换（推荐）
  python gen_html_report.py --live work/research-agent-test/live_test_results.json \
         --out work/research-agent-test/VERIFICATION_REPORT.html

  # 2) 用自定义 context JSON（任意 {{token}} 覆盖）转换
  python gen_html_report.py --context my_context.json --out out.html

  # 3) 无参数：生成一份示例报告到 report_templates/sample_report.html
  python gen_html_report.py
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, ".")
from backend.modules.html_report import render_report, from_live_json

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser(description="test-accel HTML 报告生成器")
    ap.add_argument("--live", help="live_test_results.json 路径")
    ap.add_argument("--context", help="自定义 {{token}} 覆盖 JSON 路径")
    ap.add_argument("--out", help="输出 HTML 路径（默认示例）")
    args = ap.parse_args()

    if args.live:
        html = from_live_json(args.live)
        out = Path(args.out) if args.out else ROOT / "report_templates" / "live_report.html"
    elif args.context:
        ctx = json.loads(Path(args.context).read_text(encoding="utf-8"))
        html = render_report(ctx)
        out = Path(args.out) if args.out else ROOT / "report_templates" / "context_report.html"
    else:
        html = render_report()
        out = Path(args.out) if args.out else ROOT / "report_templates" / "sample_report.html"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("written ->", out, "(%d bytes)" % len(html))


if __name__ == "__main__":
    main()
