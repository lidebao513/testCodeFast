"""命令行入口（CLI）。

    python -m cli.main pipeline --path <dir> [--mode full|incremental] [--base REF --target REF]
    python -m cli.main pipeline --url <地址> --user <账号> --password <密码> [--otp <动态口令>]
    python -m cli.main pipeline --auto-input "<一段混排文本>"
    python -m cli.main parse-input "<一段混排文本>"
    python -m cli.main analyze  --path <dir>
    python -m cli.main serve    [--host H] [--port P]

设计约定：
- CLI 是「最外层」，可依赖全部内层（core / engine / workspace / output）；
- 结构化输出走 stdout 的 JSON，人可读摘要走 stderr，便于脚本化调用；
- **统一智能输入框**：`--auto-input` 收一段混排文本（地址+账号+密码+动态口令+路径），
  由 `core.auto_input` 解析后填入选项；覆盖优先级为
  **显式参数 > 智能输入框 > 环境变量**；
- 凭证可走 `--user/--password/--otp`，但**更推荐环境变量**（命令行会留在 shell 历史里）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from core.auto_input import AutoInputResult, parse_auto_input
from core.config import get_settings
from core.db import init_db
from core.enums import (
    ALL_TP_TYPES,
    DEFAULT_SCOPE,
    DEFAULT_SCOPE_LIST,
    MODE_CHOICES,
    MODE_FULL,
)
from core.errors import AppError
from core.log import setup_logging
from engine import diff_tag, pipeline
from engine.scan import Scanner
from output.writer import OutputWriter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="testgen", description="测试用例生成服务 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pipe = sub.add_parser("pipeline", help="代码/地址 → 功能点 → 测试点 → 用例")
    pipe.add_argument("--path", default="", help="被测代码目录（可选；与 --url 至少给一个）")
    pipe.add_argument("--name", default="", help="项目名（缺省用目录名或被测主机名）")
    pipe.add_argument("--mode", default=None, choices=list(MODE_CHOICES))
    pipe.add_argument("--base", default=None, help="增量模式基线 ref")
    pipe.add_argument(
        "--target",
        default=None,
        help=f"增量模式目标 ref；给 {diff_tag.WORKTREE_TARGET} 表示与当前工作区比较（无需提交）",
    )
    pipe.add_argument(
        "--scopes",
        default=None,
        help=f"行为维度范围，逗号分隔，可选 {ALL_TP_TYPES}（默认 {'+'.join(DEFAULT_SCOPE_LIST)}）",
    )
    pipe.add_argument("--prd", default="", help="PRD / OpenAPI 文件路径（启用 PRD 通道）")
    pipe.add_argument("--no-business", action="store_true", help="不提取业务函数")
    pipe.add_argument("--no-pages", action="store_true", help="不提取前端路由")
    pipe.add_argument("--llm", action="store_true", help="启用 LLM 增强通道")
    pipe.add_argument("--no-persist", action="store_true", help="不落库（只出报告）")
    pipe.add_argument("--no-output", action="store_true", help="不写出产物文件")
    # —— 地址通道（A1）——
    pipe.add_argument("--url", default="", help="被测环境地址（走运行时 UI 发现）")
    pipe.add_argument("--login-url", default="", help="登录页地址（缺省自动判定）")
    pipe.add_argument("--user", default="", help="登录账号（更推荐 RUNTIME_LOGIN_USER）")
    pipe.add_argument("--password", default="", help="登录密码（更推荐 RUNTIME_LOGIN_PASSWORD）")
    pipe.add_argument("--otp", default="", help="动态口令（更推荐 RUNTIME_LOGIN_OTP）")
    pipe.add_argument("--route", action="append", default=[], help="显式路由，可重复")
    pipe.add_argument(
        "--runtime-ui",
        action="store_true",
        help="启用运行时 UI 发现（等价于 RUNTIME_UI_ENABLED=on）",
    )
    pipe.add_argument(
        "--auto-input",
        default="",
        help="统一智能输入框：一段混排文本（地址+账号+密码+动态口令+路径）；@文件 从文件读",
    )
    pipe.add_argument("--execute", action="store_true", help="执行生成的用例（接口层）")
    pipe.add_argument(
        "--exec-url",
        default="",
        help="执行器被测服务地址（只跑接口层时用它，无需打开浏览器通道）",
    )
    pipe.add_argument(
        "--allow-write",
        action="store_true",
        help="放行写操作（POST/PUT/PATCH/DELETE）；默认只跑只读请求，防污染被测环境",
    )

    pi = sub.add_parser("parse-input", help="只解析统一智能输入框文本（不跑流水线）")
    pi.add_argument("text", nargs="*", help="混排文本；@文件 从文件读")
    pi.add_argument("--pretty", action="store_true", help="美化 JSON 输出")

    ana = sub.add_parser("analyze", help="只做扫描 + 功能点提取")
    ana.add_argument("--path", required=True)

    srv = sub.add_parser("serve", help="启动 HTTP 服务")
    srv.add_argument("--host", default=None)
    srv.add_argument("--port", type=int, default=None)

    return p


def _parse_scopes(raw: str) -> set[str]:
    items = {s.strip() for s in raw.split(",") if s.strip()}
    invalid = items - set(ALL_TP_TYPES)
    if invalid:
        raise AppError(f"非法范围：{sorted(invalid)}，允许 {ALL_TP_TYPES}")
    return items or set(DEFAULT_SCOPE)


def _read_text(raw: str) -> str:
    """解析输入文本：`@文件` 从文件读取，否则原样返回（空则返回空串）。"""
    text = (raw or "").strip()
    if text.startswith("@"):
        return Path(text[1:]).expanduser().read_text(encoding="utf-8")
    return raw or ""


def _read_auto_input(raw: str) -> AutoInputResult | None:
    text = _read_text(raw)
    if not text.strip():
        return None
    return parse_auto_input(text)


def _report_auto_input(parsed: AutoInputResult, adopted: list[str]) -> None:
    """把解析结果摘要写到 stderr（**只输出掩码视图**，绝不回显明文凭证）。"""
    info = parsed.redacted()
    print(
        f"[auto-input] 识别字段={info['recognized']} 已采纳={adopted} 未识别={info['unknown']}",
        file=sys.stderr,
    )
    if info["has_credentials"]:
        print("[auto-input] 已获得账号+密码，将走登录态发现", file=sys.stderr)
    else:
        print("[auto-input] 未凑齐账号+密码，运行时发现将按匿名访问", file=sys.stderr)


# 显式 CLI 参数 → 选项属性（表驱动：新增参数只加一行，避免长 if 分支链）
_OPTION_FIELDS: tuple[tuple[str, str], ...] = (
    ("path", "local_path"),
    ("name", "project_name"),
    ("mode", "mode"),
    ("base", "base"),
    ("target", "target"),
    ("prd", "prd_source"),
)

# 地址通道参数 → TargetRequest 属性
_TARGET_FIELDS: tuple[tuple[str, str], ...] = (
    ("url", "base_url"),
    ("login_url", "login_url"),
    ("user", "login_user"),
    ("password", "login_password"),
    ("otp", "login_otp"),
)


def _apply_cli_target(args: argparse.Namespace, opts: pipeline.PipelineOptions) -> None:
    """把显式 CLI 参数覆盖到选项上（优先级最高）。"""
    for arg_name, attr in _OPTION_FIELDS:
        if getattr(args, arg_name, None):
            setattr(opts, attr, getattr(args, arg_name))
    if args.scopes:
        opts.scopes = _parse_scopes(args.scopes)
    req = opts.target_req
    for arg_name, attr in _TARGET_FIELDS:
        if getattr(args, arg_name, ""):
            setattr(req, attr, getattr(args, arg_name))
    if args.route:
        req.routes = [*args.route, *req.routes]
    if args.runtime_ui or args.url or args.login_url:
        req.enabled = True
    if args.exec_url:
        req.exec_url = args.exec_url
    req.execute = bool(req.execute or args.execute or args.exec_url)
    req.allow_write = bool(req.allow_write or args.allow_write)


def _cmd_pipeline(args: argparse.Namespace) -> int:
    opts = pipeline.default_options(mode=MODE_FULL)
    parsed = _read_auto_input(args.auto_input)
    if parsed is not None:
        adopted = pipeline.apply_auto_input(opts, parsed)
        _report_auto_input(parsed, adopted)
    _apply_cli_target(args, opts)

    opts.include_business = not args.no_business
    opts.extract_pages = not args.no_pages
    opts.persist = not args.no_persist
    opts.llm.enabled = args.llm and get_settings().llm_enhance

    if opts.persist:
        init_db()

    def on_progress(stage: str, info: dict[str, Any]) -> None:
        print(f"[pipeline] {stage} {info}", file=sys.stderr)

    result = pipeline.run_pipeline(opts, progress=on_progress)

    payload: dict[str, Any] = {"result": result.to_dict()}
    if result.project_id and not args.no_output:
        payload["outputs"] = OutputWriter().write_all(
            result.project_id, result.test_points, result.cases, result.to_dict()
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_parse_input(args: argparse.Namespace) -> int:
    text = _read_text(" ".join(args.text))
    parsed = parse_auto_input(text)
    payload = {
        "ok": True,
        "parsed": parsed.redacted(),
        "recognized": parsed.recognized_fields(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    from engine import fp_extract

    files = Scanner(args.path).index()
    extracted = fp_extract.extract_functional_points(files)
    print(
        json.dumps(
            {
                "path": args.path,
                "files": len(files),
                "counts": extracted.counts,
                "errors": extracted.errors[:20],
                "functional_points": [fp.to_dict() for fp in extracted.functional_points],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "service.app:app",
        host=args.host or s.host,
        port=args.port or s.port,
        reload=False,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "pipeline":
            return _cmd_pipeline(args)
        if args.cmd == "parse-input":
            return _cmd_parse_input(args)
        if args.cmd == "analyze":
            return _cmd_analyze(args)
        if args.cmd == "serve":
            return _cmd_serve(args)
    except AppError as exc:
        print(f"[error] {exc.code}: {exc.message}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
