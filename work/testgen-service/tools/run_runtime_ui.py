"""P3 工具：对给定被测地址执行一次「运行时 UI 发现」，输出 JSON 摘要到 stdout。

用法（**凭证优先走环境变量**，避免落入命令历史与进程列表）：
    RUNTIME_BASE_URL=http://host:9001/login \
    RUNTIME_LOGIN_USER=<账号> RUNTIME_LOGIN_PASSWORD=<密码> \
    PLAYWRIGHT_CHANNEL=msedge \
        venv/Scripts/python.exe tools/run_runtime_ui.py --pretty

参数可覆盖环境变量（仅限本机临时调试；会出现在命令历史里）：
    --url / --login-url / --user / --password / --route（可重复）/ --max-pages
    --headful（有头模式，便于肉眼观察） / --no-login（强制匿名） / --out <文件>

约定：stdout 只输出 JSON 结果；日志走 stderr。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import load_settings
from core.errors import AppError
from core.log import setup_logging
from engine import runtime_ui


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="P3 运行时 UI 发现（一次性）")
    p.add_argument("--url", default="", help="被测环境地址（整站源地址或登录页地址）")
    p.add_argument("--login-url", default="", help="登录页地址；默认与 --url 相同")
    p.add_argument("--user", default="", help="登录账号（建议改用 RUNTIME_LOGIN_USER）")
    p.add_argument("--password", default="", help="登录密码（建议改用 RUNTIME_LOGIN_PASSWORD）")
    p.add_argument("--route", action="append", default=[], help="显式路由，可重复；优先级最高")
    p.add_argument("--max-pages", type=int, default=0, help="遍历页面上限（0=用配置默认）")
    p.add_argument("--timeout", type=int, default=0, help="单页超时秒数（0=用配置默认）")
    p.add_argument("--headful", action="store_true", help="有头模式（调试用）")
    p.add_argument("--no-login", action="store_true", help="强制匿名访问，不提交登录表单")
    p.add_argument("--pretty", action="store_true", help="美化 JSON 输出")
    p.add_argument("--out", default="", help="同时把 JSON 写入该文件（仓库外路径）")
    return p.parse_args(argv)


def _build_options(args: argparse.Namespace) -> runtime_ui.RuntimeUiOptions:
    opts = runtime_ui.options_from_settings(load_settings())
    if args.url:
        opts.base_url = args.url
    if args.login_url:
        opts.login_url = args.login_url
    if args.user:
        opts.login_user = args.user
    if args.password:
        opts.login_password = args.password
    if args.no_login:
        opts.login_user = ""
        opts.login_password = ""
    if args.route:
        opts.routes = [*args.route, *opts.routes]
    if args.max_pages > 0:
        opts.max_pages = args.max_pages
    if args.timeout > 0:
        opts.timeout = args.timeout
    if args.headful:
        opts.headless = False
    return opts


def _summarize(result: runtime_ui.RuntimeUiResult) -> dict[str, object]:
    return {
        "base_url": result.base_url,
        "logged_in": result.logged_in,
        "degraded": result.degraded,
        "counts": {
            "pages": len(result.pages),
            "reachable": sum(1 for p in result.pages if p.reachable),
            "elements": len(result.elements),
            "console_errors": len(result.console_errors),
        },
        "pages": [
            {
                "path": page.path,
                "title": page.title,
                "reachable": page.reachable,
                "elements": len(page.elements),
                "console_errors": page.console_errors,
            }
            for page in result.pages
        ],
        "elements": [
            {"kind": e.kind, "text": e.text, "visible": e.visible, "selector": e.selector}
            for e in result.elements[:150]
        ],
        "nav_texts": [e.text for e in result.elements if e.kind == "nav" and e.text][:50],
        "notes": result.notes,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    setup_logging()
    try:
        result = runtime_ui.discover_ui(_build_options(args))
    except AppError as exc:
        payload = {"ok": False, "code": exc.code, "message": exc.message}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    text = json.dumps(
        {"ok": True, **_summarize(result)},
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
