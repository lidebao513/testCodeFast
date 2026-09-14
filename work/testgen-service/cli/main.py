"""命令行入口（CLI）。

    python -m cli.main pipeline --path <dir> [--mode full|incremental] [--base REF --target REF]
    python -m cli.main analyze  --path <dir>
    python -m cli.main serve    [--host H] [--port P]

设计约定：
- CLI 是「最外层」，可依赖全部内层（core / engine / workspace / output）；
- 结构化输出走 stdout 的 JSON，人可读摘要走 stderr，便于脚本化调用。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from core.config import get_settings
from core.db import init_db
from core.enums import ALL_TP_TYPES, DEFAULT_SCOPE, DEFAULT_SCOPE_LIST
from core.errors import AppError
from core.log import setup_logging
from engine import pipeline
from engine.scan import Scanner
from output.writer import OutputWriter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="testgen", description="测试用例生成服务 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pipe = sub.add_parser("pipeline", help="代码 → 功能点 → 测试点 → 用例")
    pipe.add_argument("--path", required=True, help="被测代码目录")
    pipe.add_argument("--name", default="", help="项目名（缺省用目录名）")
    pipe.add_argument("--mode", default="full", choices=["full", "incremental"])
    pipe.add_argument("--base", default=None, help="增量模式基线 ref")
    pipe.add_argument("--target", default=None, help="增量模式目标 ref")
    pipe.add_argument(
        "--scopes",
        default=",".join(DEFAULT_SCOPE_LIST),
        help=f"行为维度范围，逗号分隔，可选 {ALL_TP_TYPES}（默认 {'+'.join(DEFAULT_SCOPE_LIST)}）",
    )
    pipe.add_argument("--prd", default="", help="PRD / OpenAPI 文件路径（启用 PRD 通道）")
    pipe.add_argument("--no-business", action="store_true", help="不提取业务函数")
    pipe.add_argument("--no-pages", action="store_true", help="不提取前端路由")
    pipe.add_argument("--llm", action="store_true", help="启用 LLM 增强通道")
    pipe.add_argument("--no-persist", action="store_true", help="不落库（只出报告）")
    pipe.add_argument("--no-output", action="store_true", help="不写出产物文件")

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


def _cmd_pipeline(args: argparse.Namespace) -> int:
    opts = pipeline.default_options(args.path, mode=args.mode)
    opts.project_name = args.name
    opts.base = args.base
    opts.target = args.target
    opts.prd_source = args.prd
    opts.scopes = _parse_scopes(args.scopes)
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
