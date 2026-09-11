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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core import store
from core.config import get_settings
from core.contracts import CONTRACT_VERSION
from core.db import connect, init_db
from core.enums import ALL_TP_TYPES, PullStatus, TPType
from core.errors import AppError, UnauthorizedError, ValidationError
from core.log import get_logger, log_extra, set_request_id
from engine import pipeline
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
    local_path: str = Field(..., description="被测代码所在目录（绝对或相对路径）")
    project_name: str = Field("", description="项目名（缺省用目录名）")
    mode: str = Field("full", description="full=全量扫描 / incremental=增量扫描")
    base: str | None = Field(None, description="增量模式基线 ref")
    target: str | None = Field(None, description="增量模式目标 ref")
    scopes: list[str] = Field(
        default_factory=lambda: [TPType.NORMAL.value, TPType.BOUNDARY.value],
        description="行为维度范围：正常/异常/安全/边界",
    )
    include_business: bool = Field(True, description="是否提取业务函数功能点")
    extract_pages: bool = Field(True, description="是否提取前端路由")
    persist: bool = Field(True, description="是否落库")
    llm_enhance: bool = Field(False, description="是否启用 LLM 增强通道")
    readonly_lock: bool = Field(False, description="分析完成后是否把目录置只读")


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
@app.post("/api/v1/pipeline", dependencies=[Depends(require_auth)])
def run_pipeline(req: PipelineRequest) -> dict[str, Any]:
    """一站式：代码 → 功能点 → 测试点 → 用例（含落库与产物输出）。"""
    invalid = set(req.scopes or []) - set(ALL_TP_TYPES)
    if invalid:
        raise ValidationError(f"非法行为维度：{sorted(invalid)}，允许 {ALL_TP_TYPES}")

    opts = pipeline.default_options(req.local_path, mode=req.mode)
    opts.project_name = req.project_name
    opts.base = req.base
    opts.target = req.target
    opts.scopes = set(req.scopes or [])
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
                if _is_managed(req.local_path)
                else {"skipped": "外部目录未纳入工作区管理"}
            )
    return payload


class AnalyzeRequest(BaseModel):
    local_path: str
    project_name: str = ""
    include_business: bool = True
    extract_pages: bool = True


@app.post("/api/v1/analyze", dependencies=[Depends(require_auth)])
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    """只做「扫描 + 功能点提取」，不生成测试点与用例。"""
    from engine import fp_extract, scan  # 局部导入：避免服务壳顶部依赖过重

    scanner = scan.Scanner(req.local_path)
    files = scanner.index()
    extracted = fp_extract.extract_functional_points(
        files, include_business=req.include_business, extract_pages=req.extract_pages
    )
    return {
        "files": len(files),
        "counts": extracted.counts,
        "errors": extracted.errors[:20],
        "functional_points": [fp.to_dict() for fp in extracted.functional_points[:500]],
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


@app.get("/api/v1/workspaces", dependencies=[Depends(require_auth)])
def list_workspaces() -> dict[str, Any]:
    return {"workspaces": [w.to_dict() for w in WorkspaceManager().list_all()]}
