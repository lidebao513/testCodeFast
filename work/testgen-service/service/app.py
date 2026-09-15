"""服务壳（HTTP 薄壳）：只做「解析请求 → 调引擎 → 格式化响应」，不含业务逻辑。

契约：
- 版本化前缀 `/api/v1`，便于后续演进不破坏调用方；
- 统一错误结构 `{code, message, detail?}`，**不返回堆栈**；
- 每个请求分配 `request_id`，贯穿结构化日志；
- `/health`（存活）与 `/ready`（就绪）分离，便于发布流水线探活。

已知边界（有意）：当前端点**同步执行**。异步任务化 + webhook 回调属于服务化改造范围，
不在本次「代码 → 用例生成」范围（见 P0-P3 确认书 ⛔ 部分）。
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from core import store
from core.auto_input import parse_auto_input
from core.config import get_settings
from core.contracts import CONTRACT_VERSION
from core.db import connect, init_db
from core.enums import ALL_TP_TYPES, MODE_FULL, REPORT_FORMATS, PullStatus, ReportFormat
from core.errors import AppError, NotFoundError, UnauthorizedError, ValidationError
from core.log import get_logger, log_extra, set_request_id
from engine import pipeline
from engine import report as report_engine
from output.report_writer import render_html, render_markdown
from output.writer import OutputWriter
from workspace.manager import WorkspaceManager


log = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="testgen-service",
    version="0.1.0",
    description="测试用例生成服务：代码解析 → 测试点 → 用例（契约 v1.0）",
)


# ============================================================================
# 中间件 / 错误处理
# ============================================================================
@app.middleware("http")
async def request_context(request: Request, call_next: Any) -> Any:
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    set_request_id(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    log.warning("业务异常", extra=log_extra(code=exc.code, message=exc.message))
    return JSONResponse(status_code=exc.http_status, content=exc.to_payload())


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    """兜底：只暴露类型名，绝不返回堆栈或内部细节。"""
    log.error("未处理异常", extra=log_extra(err=type(exc).__name__), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "服务内部错误"},
    )


# ============================================================================
# 鉴权（占位实现：配置了 AUTH_TOKEN 才校验）
# ============================================================================
def require_auth(
    x_auth_token: Annotated[str | None, Header(alias="X-Auth-Token")] = None,
) -> None:
    if not settings.auth_token:
        return
    if x_auth_token != settings.auth_token:
        raise UnauthorizedError("缺少或无效的 X-Auth-Token")


AuthDep = Annotated[None, Depends(require_auth)]


def _is_managed(local_path: str) -> bool:
    """目标目录是否位于工作区根内（只有受管目录才做只读加固）。"""
    try:
        WorkspaceManager().assert_inside(local_path)
    except AppError:
        return False
    return True


# ============================================================================
# 请求模型
# ============================================================================
class PipelineRequest(BaseModel):
    local_path: str = Field("", description="被测代码所在目录（可选；与 test_url 至少给一个）")
    repo_url: str = Field(
        "", description="仓库地址（F1）：先取码到 local_path（缺省落到工作区根/仓库名）"
    )
    pull_deepen: int = Field(0, ge=0, description="浅克隆加深的提交数（0=不加深）")
    changed_files: list[str] = Field(
        default_factory=list,
        description="显式变更文件清单（F2，正斜杠相对路径）；优先于本地 git diff",
    )
    project_name: str = Field("", description="项目名（缺省用目录名或被测主机名）")
    mode: str = Field("", description="full=全量扫描 / incremental=增量扫描（留空=默认 full）")
    base: str | None = Field(None, description="增量模式基线 ref")
    target: str | None = Field(None, description="增量模式目标 ref")
    scopes: list[str] = Field(
        default_factory=list,
        description="行为维度范围：正常/异常/安全/边界（留空=默认 正常+安全+边界）",
    )
    prd_source: str = Field("", description="PRD / OpenAPI 文件路径（启用 PRD 通道时使用）")
    include_business: bool = Field(True, description="是否提取业务函数功能点")
    extract_pages: bool = Field(True, description="是否提取前端路由")
    persist: bool = Field(True, description="是否落库")
    llm_enhance: bool = Field(False, description="是否启用 LLM 增强通道")
    readonly_lock: bool = Field(False, description="分析完成后是否把目录置只读")
    # —— 地址通道（A1）：凭证字段只用于本次运行，**绝不回显、不落库、不入产物** ——
    test_url: str = Field("", description="被测环境地址（走运行时 UI 发现）")
    login_url: str = Field("", description="登录页地址（缺省自动判定）")
    login_user: str = Field("", description="登录账号（更推荐用环境变量注入）")
    login_password: str = Field("", description="登录密码（更推荐用环境变量注入）")
    login_otp: str = Field("", description="动态口令（更推荐用环境变量注入）")
    runtime_routes: list[str] = Field(default_factory=list, description="显式路由（优先级最高）")
    runtime_ui: bool = Field(False, description="启用运行时 UI 发现（等价 RUNTIME_UI_ENABLED=on）")
    auto_input: str = Field("", description="统一智能输入框：一段混排文本（地址+账号+密码+口令）")
    execute: bool = Field(False, description="执行生成的用例（接口层 + UI 层）")
    allow_write: bool = Field(False, description="放行写操作；默认只跑只读请求")
    ui_click: bool = Field(False, description="UI 层执行真实点击（F13）；默认只做只读断言")
    exec_url: str = Field("", description="执行器被测服务地址（只跑接口层时可单独指定）")


class ParseInputRequest(BaseModel):
    """统一智能输入框解析请求（只解析、不跑流水线）。"""

    text: str = Field("", description="混排文本：地址 / 账号 / 密码 / 动态口令 / 代码路径")


# ============================================================================
# 基础端点
# ============================================================================
@app.get("/health")
def health() -> dict[str, Any]:
    """存活探针：进程活着即 200。"""
    return {
        "status": PullStatus.OK.value,
        "service": "testgen-service",
        "contract_version": CONTRACT_VERSION,
    }


@app.get("/ready")
def ready() -> dict[str, Any]:
    """就绪探针：数据库可用即 200。"""
    try:
        init_db()
        conn = connect()
        conn.execute("SELECT 1")
        conn.close()
    except Exception as exc:  # noqa: BLE001 - 就绪检查需兜住一切异常并如实上报
        return {"status": "not_ready", "detail": type(exc).__name__}
    return {"status": "ready", "config": settings.public_dict()}


# ============================================================================
# 业务端点 v1
# ============================================================================
def _apply_code_sources(req: PipelineRequest, opts: pipeline.PipelineOptions) -> None:
    """把「代码来源类」字段覆盖到选项（F1 仓库地址 / F2 变更清单 / 模式 / 基线）。"""
    for attr in ("project_name", "mode", "base", "target", "prd_source", "repo_url"):
        value = getattr(req, attr, None)
        if value:
            setattr(opts, attr, value)
    if req.scopes:
        opts.scopes = set(req.scopes)
    # F2：显式变更文件清单（统一正斜杠，与 git diff 输出形态对齐）
    files = [str(f).strip().replace("\\", "/") for f in req.changed_files if str(f).strip()]
    if files:
        opts.changed_files = files
    if req.pull_deepen:
        opts.pull_deepen = int(req.pull_deepen)


def _apply_request(req: PipelineRequest, opts: pipeline.PipelineOptions) -> None:
    """把请求字段覆盖到选项上（表驱动）。

    顺序即优先级：调用方须先让智能输入框填（可覆盖默认值），再调本函数（覆盖输入框）。
    """
    _apply_code_sources(req, opts)
    target = opts.target_req
    for attr, value in (
        ("base_url", req.test_url),
        ("login_url", req.login_url),
        ("login_user", req.login_user),
        ("login_password", req.login_password),
        ("login_otp", req.login_otp),
    ):
        if value:
            setattr(target, attr, value)
    if req.runtime_routes:
        target.routes = [*req.runtime_routes, *target.routes]
    if req.runtime_ui or req.test_url or req.login_url:
        target.enabled = True
    if req.exec_url:
        target.exec_url = req.exec_url
    target.execute = req.execute or bool(req.exec_url)
    target.allow_write = req.allow_write
    target.ui_click = req.ui_click


@app.post("/api/v1/pipeline", dependencies=[Depends(require_auth)])
def run_pipeline(req: PipelineRequest) -> dict[str, Any]:
    """一站式：代码/地址 → 功能点 → 测试点 → 用例（含落库与产物输出）。

    两条入口可单用也可并用：`local_path`（代码通道）与 `test_url`（地址通道）。
    覆盖优先级：**请求字段 > auto_input 解析结果 > 环境变量**。
    """
    invalid = set(req.scopes or []) - set(ALL_TP_TYPES)
    if invalid:
        raise ValidationError(f"非法行为维度：{sorted(invalid)}，允许 {ALL_TP_TYPES}")

    opts = pipeline.default_options(req.local_path, mode=req.mode or MODE_FULL)
    if req.auto_input.strip():
        pipeline.apply_auto_input(opts, parse_auto_input(req.auto_input))
    _apply_request(req, opts)
    opts.include_business = req.include_business
    opts.extract_pages = req.extract_pages
    opts.persist = req.persist
    opts.llm.enabled = bool(req.llm_enhance and settings.llm_enhance)

    result = pipeline.run_pipeline(opts)

    payload: dict[str, Any] = {"result": result.to_dict()}
    if result.project_id:
        outputs = OutputWriter().write_all(
            result.project_id, result.test_points, result.cases, result.to_dict()
        )
        payload["outputs"] = outputs
        if req.readonly_lock:
            payload["readonly"] = (
                WorkspaceManager().lock(Path(req.local_path).name, verify=True)
                if req.local_path and _is_managed(req.local_path)
                else {"skipped": "外部目录未纳入工作区管理"}
            )
    return payload


@app.post("/api/v1/parse-input", dependencies=[Depends(require_auth)])
def parse_input(req: ParseInputRequest) -> dict[str, Any]:
    """统一智能输入框：只解析混排文本，返回**掩码视图**（可用于前端实时预览）。

    绝不回显明文凭证——前端据此确认「识别对不对」，而不是把密码再抄一遍。
    """
    parsed = parse_auto_input(req.text)
    return {
        "recognized": parsed.recognized_fields(),
        "parsed": parsed.redacted(),
    }


class AnalyzeRequest(BaseModel):
    local_path: str
    project_name: str = ""
    include_business: bool = True
    extract_pages: bool = True


class PullRequest(BaseModel):
    """取码请求（F1）：把仓库准备到本地并（可选）算出变更集。

    与 `/api/v1/pipeline` 的 `repo_url` 的区别：本端点**只取码**、不跑生成链路——
    供上游平台在触发流水线前先确认「代码拿到了、变更集对不对」。凭证只在本请求内传递。
    """

    repo_url: str = Field("", description="仓库地址（含凭证时结果与日志一律掩码）")
    local_path: str = Field("", description="本地目标目录；缺省落到工作区根/仓库名（受管目录）")
    base: str = Field("", description="基线 ref（与 target 一起算变更集）")
    target: str = Field("", description="目标 ref；WORKTREE 表示与当前工作区比较")
    deepen: int = Field(0, ge=0, description="浅克隆加深的提交数（0=不加深）")


@app.post("/api/v1/pull", dependencies=[Depends(require_auth)])
def pull_code(req: PullRequest) -> dict[str, Any]:
    """取码（F1）：克隆 / 更新 / 加深 / 算变更集。

    失败**不抛 5xx**：取码失败是常见业务结果（远端不可达、非空目录、ref 失效），
    以 `success=false` + `status` 如实返回，调用方据 `status` 决策。
    凭证（URL 中的 user:token）在返回结果中**一律掩码**。
    """
    import os

    from engine import pull as pull_engine

    url = req.repo_url or (os.environ.get("REPO_URL") or "").strip()
    local_path = req.local_path or str(settings.workspace_root / pipeline.repo_dir_name(url))
    result = pull_engine.pull(url, local_path, base=req.base, target=req.target, deepen=req.deepen)
    return {"pull": result.to_dict()}


@app.post("/api/v1/analyze", dependencies=[Depends(require_auth)])
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    """只做「扫描 + 功能点提取」，不生成测试点与用例。

    应用与流水线**同一套**功能点语义合并口径（F5），否则同一份代码经 `/analyze`
    与 `/pipeline` 会得到两个不同的功能点数——那是最难排查的一类「数字不一致」。
    """
    from engine import fp_extract, fp_merge, scan  # 局部导入：避免服务壳顶部依赖过重

    scanner = scan.Scanner(req.local_path)
    files = scanner.index()
    extracted = fp_extract.extract_functional_points(
        files, include_business=req.include_business, extract_pages=req.extract_pages
    )
    fps = extracted.functional_points
    merge_stats: dict[str, Any] = {"deduped": 0}
    if settings.fp_semantic_merge:
        fps, merge_stats = fp_merge.dedupe_functional_points(fps)
    counts: dict[str, int] = {}
    for fp in fps:
        counts[fp.ftype] = counts.get(fp.ftype, 0) + 1
    return {
        "files": len(files),
        "counts": counts,
        "fp_semantic_merge": {
            "rule_version": fp_merge.MERGE_RULE_VERSION,
            "deduped": int(merge_stats.get("deduped", 0)),
            "examples": list(merge_stats.get("examples") or []),
        },
        "errors": extracted.errors[:20],
        "functional_points": [fp.to_dict() for fp in fps[:500]],
    }


@app.get("/api/v1/projects", dependencies=[Depends(require_auth)])
def list_projects() -> dict[str, Any]:
    return {"projects": store.list_projects()}


@app.get("/api/v1/projects/{pid}/test-points", dependencies=[Depends(require_auth)])
def get_test_points(pid: int) -> dict[str, Any]:
    return {"project_id": pid, "test_points": store.list_test_points(pid)}


@app.get("/api/v1/projects/{pid}/cases", dependencies=[Depends(require_auth)])
def get_cases(pid: int, include_obsolete: bool = False) -> dict[str, Any]:
    return {
        "project_id": pid,
        "cases": store.list_cases(pid, include_obsolete=include_obsolete),
    }


@app.get("/api/v1/projects/{pid}/traceability", dependencies=[Depends(require_auth)])
def get_traceability(pid: int) -> dict[str, Any]:
    return {"project_id": pid, "traceability": store.traceability(pid)}


@app.get("/api/v1/projects/{pid}/runs", dependencies=[Depends(require_auth)])
def get_runs(pid: int, limit: int = 50) -> dict[str, Any]:
    """执行批次列表（F12 留痕）：最新在前，含状态分布与批次终态。"""
    batches = store.list_run_batches(pid, limit=limit)
    return {"project_id": pid, "batches": batches, "latest": batches[0] if batches else None}


@app.get("/api/v1/projects/{pid}/runs/{batch_id}", dependencies=[Depends(require_auth)])
def get_run_detail(pid: int, batch_id: str, limit: int = 500) -> dict[str, Any]:
    """单批次详情：批次终态 + 逐条执行结论（`cases.last_result` 的来源）。"""
    batch = store.get_run_batch(batch_id)
    if batch is None or int(batch.get("project_id") or 0) != pid:
        raise NotFoundError(f"执行批次不存在：{batch_id}")
    return {
        "project_id": pid,
        "batch": batch,
        "runs": store.list_runs(pid, batch_id=batch_id, limit=limit),
    }


@app.get("/api/v1/projects/{pid}/report", dependencies=[Depends(require_auth)])
def get_report(
    pid: int, batch: str = "", format: str = ReportFormat.JSON.value, write: bool = False
):
    """项目报告（F15）：执行摘要 + 覆盖率 + 趋势 + 追溯 + 执行证据。

    - `format=json`（默认）→ 返回报告结构（机读，含全部字段）；
    - `format=md` → 直接返回可交付 Markdown；`format=html` → 返回自包含浅色页面；
    - `write=true` → 同时把 `REPORT.md` / `REPORT.html` / `report.json` 落到 `outputs/<pid>/`。

    报告是 DB 事实的**纯函数**（取数 `store.report_snapshot` → 计算 `engine.report`），
    不新建报告表——同一份数据任意时刻重算结论一致。
    """
    fmt = (format or "").strip().lower()
    if fmt not in REPORT_FORMATS:
        raise ValidationError(f"不支持的报告格式：{format!r}，允许 {list(REPORT_FORMATS)}")
    built = report_engine.generate(pid, batch_id=batch, write=write)
    body = built["report"]
    if fmt == ReportFormat.MARKDOWN.value:
        return Response(content=render_markdown(body), media_type="text/markdown; charset=utf-8")
    if fmt == ReportFormat.HTML.value:
        return HTMLResponse(content=render_html(body))
    payload: dict[str, Any] = {"project_id": pid, "report": body}
    if built["outputs"]:
        payload["outputs"] = built["outputs"]
    return payload


@app.get("/api/v1/projects/{pid}/coverage", dependencies=[Depends(require_auth)])
def get_coverage(pid: int) -> dict[str, Any]:
    """覆盖率视图（F16）：功能点 → 测试点 → 用例，含未覆盖缺口。"""
    snapshot = store.report_snapshot(pid)
    if not snapshot.get("project"):
        raise NotFoundError(f"项目不存在：{pid}")
    return {
        "project_id": pid,
        "coverage": report_engine.coverage(
            snapshot["functional_points"], snapshot["test_points"], snapshot["cases"]
        ),
    }


@app.get("/api/v1/workspaces", dependencies=[Depends(require_auth)])
def list_workspaces() -> dict[str, Any]:
    return {"workspaces": [w.to_dict() for w in WorkspaceManager().list_all()]}
