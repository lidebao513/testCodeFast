"""引擎 · 编排（pipeline）：把六个模块串成一条可复现的流水线。

    扫描 → 功能点提取 → 差异打标 → 测试点展开 → 语义增强 → 用例生成 → 落库

设计要点：
- **每个阶段一个函数**：输入输出都是显式数据，便于单测与影子双跑比对；
- **全量 / 增量同一条链路**，差异只体现在「是否传入 diff 上下文」；
- 任一阶段失败都带上下文抛出（`EngineError`），不吞异常。
- **可选扩展阶段（P2/P3）默认关闭**：由 Settings 的 flag 守卫；其中 P3 运行时
  UI 发现失败**只记错误不阻断主链路**（见 `P3_UI生成_详细设计.md` §10）。

两条入口（A1 · 见 `两条生成流程_链路梳理与补齐方案.md`）
---------------------------------------------------------
1. **代码通道**：`local_path` 指向被测代码目录 → 静态扫描 → 功能点 → 测试点 → 用例；
2. **地址通道**：`target.base_url` + 账号密码 → 运行时 UI 发现 → 功能点 → 测试点 → 用例。
   两者可**同时提供**：地址通道发现的功能点按 `(ftype, name)` 并入静态集合（运行时优先），
   用例正文由 A2 用真实路由 / 元素 / 控制台基线富化。

   `local_path` 因此改为**可选**：既没有代码目录、也没开运行时发现时，入口直接报错
   （宁快速失败，不做一次「什么都没分析」的空跑）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core import store
from core.config import get_settings
from core.contracts import CaseSpec, FunctionalPoint, TestPoint
from core.db import init_db
from core.enums import DEFAULT_SCOPE, FType, Tag, VerifyLayer
from core.errors import EngineError, WorkspaceEscapeBlocked
from core.log import get_logger, log_extra
from engine import (
    case_gen,
    diff_tag,
    executor,
    fp_extract,
    prd_ingest,
    runtime_ui,
    scan,
    semantic_enrich,
    tp_expand,
)
from engine.scan import SourceFile


log = get_logger(__name__)

ProgressFn = Callable[[str, dict[str, Any]], None]


# ============================================================================
# 输入 / 输出
# ============================================================================
@dataclass
class TargetRequest:
    """「测试地址 + 账号密码」通道的**请求级**参数（优先级高于环境变量）。

    为什么要有请求级：环境变量只适合「一个人一台机器跑固定环境」；一旦要接入
    HTTP 调用或流水线，地址与账号必须能**按次传入**。凭证只在本对象内传递，
    **不进日志、不进产物、不落库**（与 `core.config` 同一红线）。
    """

    enabled: bool = False  # 是否启用运行时 UI 发现（等价于请求级 RUNTIME_UI_ENABLED）
    base_url: str = ""
    login_url: str = ""
    login_user: str = ""
    login_password: str = ""
    login_otp: str = ""
    routes: list[str] = field(default_factory=list)  # 显式路由（优先级最高）
    # —— 执行器（A3）——
    execute: bool = False  # 请求级开启用例执行
    allow_write: bool = False  # 是否放行写操作（默认否）
    # 执行器专用的被测服务地址。为什么要单独一个字段：接口层执行只需要 HTTP 地址，
    # **不该被迫打开浏览器通道**（打开就意味着要装 Playwright、要登录态、要遍历页面）。
    # 未设置时回落到运行时发现的 base_url。
    exec_url: str = ""


@dataclass
class PipelineOptions:
    """一次运行的完整输入。"""

    local_path: str = ""  # 可选：纯地址通道（运行时 UI 发现）不需要代码目录
    project_name: str = ""
    project_id: int | None = None
    mode: str = "full"  # full | incremental
    base: str | None = None
    target: str | None = None
    prd_source: str = ""  # P2：PRD 文件路径（启用 PRD 通道时读取）
    scopes: set[str] = field(default_factory=lambda: set(DEFAULT_SCOPE))
    review_status: str = "pending"
    include_business: bool = True
    extract_pages: bool = True
    llm: semantic_enrich.EnrichOptions = field(default_factory=semantic_enrich.EnrichOptions)
    persist: bool = True
    # 「URL + 账号密码」通道的请求级参数（A1）
    target_req: TargetRequest = field(default_factory=TargetRequest)

    @property
    def is_incremental(self) -> bool:
        return self.mode == "incremental"


@dataclass
class PipelineResult:
    """一次运行的结果摘要（可序列化，供 API / CLI 输出）。"""

    project_id: int | None = None
    mode: str = "full"
    source_kind: str = ""  # code / url / code+url（本次用了哪条入口）
    counts: dict[str, int] = field(default_factory=dict)
    scope_summary: dict[str, int] = field(default_factory=dict)
    tag_summary: dict[str, int] = field(default_factory=dict)
    case_stats: dict[str, Any] = field(default_factory=dict)
    traceability: dict[str, Any] = field(default_factory=dict)
    execution: dict[str, Any] = field(default_factory=dict)  # A3：执行结论汇总
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    # 产物本体（不参与 to_dict 序列化，供调用方写出文件）
    functional_points: list[FunctionalPoint] = field(default_factory=list, repr=False)
    test_points: list[TestPoint] = field(default_factory=list, repr=False)
    cases: list[CaseSpec] = field(default_factory=list, repr=False)
    prd_doc: Any = None  # P2：解析后的 PRD（PrdDoc），未启用为 None
    runtime_ui: Any = None  # P3：运行时 UI 发现结果（RuntimeUiResult），未启用为 None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "mode": self.mode,
            "source_kind": self.source_kind,
            "counts": self.counts,
            "scope_summary": self.scope_summary,
            "tag_summary": self.tag_summary,
            "case_stats": self.case_stats,
            "traceability": self.traceability,
            "execution": self.execution,
            "notes": self.notes,
            "errors": self.errors,
        }


def _emit(progress: ProgressFn | None, stage: str, **info: Any) -> None:
    if progress:
        progress(stage, info)


def _count_by(items: list[Any], key: Callable[[Any], str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for it in items:
        k = key(it)
        out[k] = out.get(k, 0) + 1
    return out


# ============================================================================
# 阶段 0：项目注册
# ============================================================================
def _default_project_name(opts: PipelineOptions) -> str:
    """项目名兜底：优先代码目录名，纯地址通道取被测主机名（便于按环境区分）。"""
    if opts.local_path:
        return Path(opts.local_path).name
    host = urlparse(opts.target_req.base_url).netloc
    return host or "url-target"


def stage_register(opts: PipelineOptions, result: PipelineResult) -> None:
    if opts.persist:
        init_db()
        name = opts.project_name or _default_project_name(opts)
        source = opts.local_path or opts.target_req.base_url
        result.project_id = store.upsert_project(name, source)
    elif opts.project_id is not None:
        result.project_id = opts.project_id


# ============================================================================
# 阶段 1：扫描
# ============================================================================
def stage_scan(
    opts: PipelineOptions, result: PipelineResult, progress: ProgressFn | None
) -> dict[str, SourceFile]:
    _emit(progress, "scan", path=opts.local_path)
    files = scan.Scanner(opts.local_path).index()
    result.counts["files"] = len(files)
    log.info("扫描完成", extra=log_extra(files=len(files)))
    return files


# ============================================================================
# 阶段 2：功能点提取
# ============================================================================
def stage_extract(
    opts: PipelineOptions,
    result: PipelineResult,
    files: dict[str, SourceFile],
    progress: ProgressFn | None,
) -> list[FunctionalPoint]:
    _emit(progress, "fp_extract", files=len(files))
    cfg = get_settings()
    extracted = fp_extract.extract_functional_points(
        files,
        include_business=opts.include_business,
        extract_pages=opts.extract_pages,
        business_extract_mode=cfg.business_extract_mode,
        business_include_dirs=cfg.business_include_dirs,
    )
    result.counts["functional_points"] = len(extracted.functional_points)
    result.errors.extend(extracted.errors[:20])
    return extracted.functional_points


# ============================================================================
# 阶段 3：差异打标
# ============================================================================
def _build_diff_context(opts: PipelineOptions) -> tuple[diff_tag.DiffContext, list[str]]:
    """构造差异上下文；异常一律**降级为全量**并记录，不阻断主链路。"""
    notes: list[str] = []
    if not opts.is_incremental:
        notes.append("全量通道：不做 diff，全部标为『全量』")
        return diff_tag.DiffContext(), notes
    try:
        ctx = diff_tag.build_context(opts.local_path, opts.base, opts.target)
    except WorkspaceEscapeBlocked as exc:
        raise EngineError(f"增量通道被阻断：{exc.message}") from exc
    except (ValueError, OSError) as exc:
        notes.append(f"增量通道不可用（{exc}），已降级为全量")
        return diff_tag.DiffContext(), notes
    notes.append(
        f"增量通道：变更文件 {len(ctx.changed_files)} 个，hunk 覆盖 {len(ctx.hunks)} 个文件"
    )
    return ctx, notes


def stage_tag(
    opts: PipelineOptions,
    result: PipelineResult,
    fps: list[FunctionalPoint],
    progress: ProgressFn | None,
) -> tuple[diff_tag.DiffContext, dict[str, str]]:
    _emit(progress, "diff_tag", mode=opts.mode)
    ctx, notes = _build_diff_context(opts)
    result.notes.extend(notes)
    tag_by_fp: dict[str, str] = {}
    for fp in fps:
        tag = diff_tag.tag_of_rel(fp.file_path, ctx)
        tag_by_fp[fp.fp_id] = tag
        fp.commit_ref = (opts.target or "") if tag == Tag.UPDATE.value else ""
    return ctx, tag_by_fp


# ============================================================================
# 阶段 4：测试点展开
# ============================================================================
def stage_test_points(
    opts: PipelineOptions,
    result: PipelineResult,
    fps: list[FunctionalPoint],
    tag_by_fp: dict[str, str],
    progress: ProgressFn | None,
) -> list[TestPoint]:
    _emit(progress, "tp_expand", fp=len(fps))
    ctx = tp_expand.ExpandContext(scopes=set(opts.scopes), review_status=opts.review_status)
    tps = tp_expand.expand_all(fps, ctx, tag_by_fp=tag_by_fp)
    result.counts["test_points"] = len(tps)
    result.scope_summary = tp_expand.scope_summary(tps)
    result.tag_summary = _count_by(tps, lambda t: t.tag)
    return tps


# ============================================================================
# 阶段 5：语义增强
# ============================================================================
def stage_enrich(
    opts: PipelineOptions,
    result: PipelineResult,
    tps: list[TestPoint],
    fps: list[FunctionalPoint],
    progress: ProgressFn | None,
) -> list[TestPoint]:
    _emit(progress, "semantic_enrich", enabled=opts.llm.enabled)
    enriched = semantic_enrich.enrich(tps, fps, opts.llm)
    result.counts["test_points"] = len(enriched.test_points)
    result.counts["llm_added"] = len(enriched.added)
    result.counts["llm_rejected"] = len(enriched.rejected)
    result.notes.extend(enriched.notes)
    result.scope_summary = tp_expand.scope_summary(enriched.test_points)
    return enriched.test_points


# ============================================================================
# 阶段 5.5（P2）：PRD 通道 + LLM 用例设计
# ============================================================================
def stage_prd_ingest(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
) -> Any | None:
    """P2：解析 PRD / OpenAPI 为结构化需求（真实实现），返回 PrdDoc。"""
    _emit(progress, "prd_ingest", source=opts.prd_source)
    if not opts.prd_source:
        return None
    doc = prd_ingest.ingest_prd(opts.prd_source)
    log.info("PRD 解析完成", extra=log_extra(fmt=doc.fmt, requirements=len(doc.requirements)))
    return doc


def _merge_prd_test_points(result: PipelineResult) -> None:
    """把 PRD 需求派生的测试点并入主链路（仅在 PRD 通道启用时调用）。

    未对齐到功能点的需求**不臆造**测试点，只把提示记入 result.notes（见 prd_ingest）。
    """
    if result.prd_doc is None:
        return
    prd_tps = prd_ingest.requirements_to_test_points(result.prd_doc, result.functional_points)
    result.notes.extend(result.prd_doc.notes)
    if not prd_tps:
        return
    result.test_points = [*result.test_points, *prd_tps]
    result.counts["prd_test_points"] = len(prd_tps)
    result.scope_summary = tp_expand.scope_summary(result.test_points)


def stage_llm_design(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
) -> list[CaseSpec]:
    """P2 接入点：基于功能点 + PRD 上下文设计用例（当前为骨架，原样返回）。"""
    _emit(progress, "llm_design", enabled=True)
    return result.cases


# ============================================================================
# 阶段 5.7（P3）：运行时 UI 发现 + 用例执行
# ============================================================================
def _static_page_paths(fps: list[FunctionalPoint]) -> list[str]:
    """路由优先级第 2 档：静态分析已提取的页面路径（形如 `/pc/tasks`）。"""
    return [
        str(fp.name)
        for fp in fps
        if fp.ftype in (FType.PAGE.value, FType.UI.value) and str(fp.name).startswith("/")
    ]


def _runtime_target(
    opts: PipelineOptions, settings: Any
) -> tuple[runtime_ui.RuntimeUiOptions, bool]:
    """合并「请求级参数」与「环境变量」得到运行时选项；返回 (选项, 是否启用)。

    优先级：**请求级 > 环境变量**。请求级只覆盖**非空**字段，避免把环境里的其它配置抹掉。
    启用却发现没有被测地址时直接报错——静默跳过会产出一份「看起来有 UI 用例但全是登录页」
    的假产物，比报错危险得多。
    """
    options = runtime_ui.options_from_settings(settings)
    req = opts.target_req
    for name in ("base_url", "login_url", "login_user", "login_password", "login_otp"):
        value = str(getattr(req, name, "") or "")
        if value:
            setattr(options, name, value)
    if req.routes:
        options.routes = [*req.routes, *options.routes]
    enabled = bool(req.enabled or settings.runtime_ui_enabled)
    if enabled and not options.base_url:
        raise EngineError("启用运行时 UI 发现必须提供被测地址（--url / RUNTIME_BASE_URL）")
    return options, enabled


def stage_runtime_ui(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
    runtime_options: runtime_ui.RuntimeUiOptions,
) -> Any | None:
    """P3：运行时浏览器 UI 发现（真实实现，里程碑 M3.1–M3.3）。

    用 Playwright 打开被测环境、以账号密码（+ 动态口令）登录、遍历路由抓取真实可交互元素，
    结果挂到 `result.runtime_ui` 并计入 counts。

    **本阶段只负责「发现」**：把发现的 UI 功能点并入功能点集合并参与测试点展开属 M3.4，
    用例正文富化属 A2，requests 降级属 M3.5。
    凭证经「请求级参数 / .env」注入，不落库、不入产物。
    """
    _emit(progress, "runtime_ui", base_url=runtime_options.base_url)
    found = runtime_ui.discover_ui(
        runtime_options,
        static_paths=_static_page_paths(result.functional_points),
    )
    result.runtime_ui = found
    result.notes.extend(f"运行时 UI：{n}" for n in found.notes)
    result.counts["runtime_ui_pages"] = len(found.pages)
    result.counts["runtime_ui_reachable"] = sum(1 for p in found.pages if p.reachable)
    result.counts["runtime_ui_elements"] = len(found.elements)
    result.counts["runtime_ui_routes"] = len(found.discovered_routes)
    return found


def _merge_runtime_fps(
    static_fps: list[FunctionalPoint], runtime_fps: list[FunctionalPoint]
) -> tuple[list[FunctionalPoint], dict[str, int]]:
    """把运行时发现的 UI 功能点并入静态功能点集合（M3.4）。

    去重键 = `(ftype, name)` **而非** `fp_id`：静态与运行时的 `file_path` 不同
    （静态是真实源码路径，运行时是 `runtime:<url>`），`fp_id` 必然不同，
    但语义上是同一个 UI 面（如同一路径 `/pc/tasks`）——只有按 (ftype, name) 才能正确判重。
    冲突时**运行时优先**（运行时是线上真实可达面，静态可能过时）。
    返回 (合并后的集合, 统计)。
    """
    stats = {"added": 0, "replaced": 0}
    index: dict[tuple[str, str], int] = {}
    merged: list[FunctionalPoint] = []
    for fp in static_fps:
        index[(fp.ftype, fp.name)] = len(merged)
        merged.append(fp)
    for fp in runtime_fps:
        key = (fp.ftype, fp.name)
        pos = index.get(key)
        if pos is None:
            index[key] = len(merged)
            merged.append(fp)
            stats["added"] += 1
        else:
            merged[pos] = fp
            stats["replaced"] += 1
    return merged, stats


def stage_execute(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
    runtime_options: runtime_ui.RuntimeUiOptions,
) -> dict[str, Any]:
    """P3：执行已生成的用例（A3：接口层真实执行，UI 层仍为桩）。

    地址与凭证取「请求级 > 环境变量」同一套优先级：接口层执行用的是**被测服务地址**
    （`RUNTIME_BASE_URL`），不是登录页——登录页是浏览器通道才需要的概念。
    """
    s = get_settings()
    _emit(progress, "execute", cases=len(result.cases))
    exec_options = executor.ExecutorOptions(
        base_url=opts.target_req.exec_url or runtime_options.base_url,
        auth_token=runtime_options.auth_token or s.runtime_auth_token,
        timeout=runtime_options.timeout,
        allow_write=bool(opts.target_req.allow_write or s.executor_allow_write),
    )
    summary = executor.execute_all(result.cases, exec_options)
    result.execution = summary
    for key in ("total", "executed", "pass", "fail", "error", "skipped"):
        result.counts[f"exec_{key}"] = int(summary.get(key, 0))
    result.notes.append(
        f"执行结论：共 {summary['total']} 条，已执行 {summary['executed']} 条"
        f"（通过 {summary['pass']} / 失败 {summary['fail']} / 异常 {summary['error']}），"
        f"跳过 {summary['skipped']} 条（UI 层待实现、非 HTTP 来源或写操作未放行）"
    )
    return summary


# ============================================================================
# 阶段 6：用例生成
# ============================================================================
def stage_cases(
    result: PipelineResult, tps: list[TestPoint], progress: ProgressFn | None
) -> list[CaseSpec]:
    _emit(progress, "case_gen", tp=len(tps))
    s = get_settings()
    # 已有 UI 覆盖的模块集合：用于判定接口层用例是否仅为「补充」
    ui_modules = {
        fp.module
        for fp in result.functional_points
        if fp.ftype in (FType.PAGE.value, FType.COMPONENT.value, FType.UI.value)
    }
    # A2：运行时发现的页面细节 → 用例正文富化（未启用运行时通道时为空字典，行为不变）
    runtime_index = runtime_ui.to_runtime_index(result.runtime_ui)
    cases = case_gen.generate_cases(
        tps,
        ui_modules=ui_modules,
        strategy=s.layer_strategy,
        drop_supplement=s.drop_supplement_cases,
        runtime_index=runtime_index,
    )
    result.counts["cases_with_runtime_detail"] = sum(
        1 for c in cases if c.steps and c.steps[0].get("runtime")
    )
    # UI 优先排序：UI 层用例置于接口层之前，同层按模块+编号稳定排序
    layer_rank = {VerifyLayer.UI.value: 0, VerifyLayer.INTERFACE.value: 1}
    cases.sort(
        key=lambda c: (
            layer_rank.get(str(c.steps[0].get("layer")) if c.steps else "", 1),
            c.module,
            c.tc_no,
        )
    )
    result.counts["cases"] = len(cases)
    bad = [c.tc_no for c in cases if c.missing_elements()]
    if bad:
        result.errors.append(f"{len(bad)} 条用例八要素不全（示例 {bad[:3]}）")
    return cases


# ============================================================================
# 阶段 7：落库（幂等）
# ============================================================================
def _persist_without_db(
    result: PipelineResult, tps: list[TestPoint], cases: list[CaseSpec]
) -> None:
    result.case_stats = {"created": len(cases), "updated": 0, "reused": 0, "obsolete": 0}
    result.traceability = case_gen.coverage_of(cases, tps)


def stage_persist(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
) -> None:
    """落库：读取 `result` 上已挂载的三层产物。"""
    fps = result.functional_points
    tps = result.test_points
    cases = result.cases
    if not (opts.persist and result.project_id):
        _persist_without_db(result, tps, cases)
        return

    pid = result.project_id
    _emit(progress, "persist", project_id=pid)
    with store.connect() as conn:
        init_db(conn)
        store.replace_functional_points(pid, fps, conn=conn)
        store.replace_test_points(pid, tps, conn=conn)
        fp_rows = store.fp_row_map(pid, conn)
        for case in cases:
            case.fp_row_id = fp_rows.get(case.fp_contract_id)
        result.case_stats = store.reconcile_cases(pid, cases, conn=conn)
        result.traceability = store.traceability(pid, conn=conn)
        store.log_change(
            pid,
            "pipeline",
            f"mode={opts.mode} fp={len(fps)} tp={len(tps)} case={len(cases)}",
            conn=conn,
        )


# ============================================================================
# 主入口
# ============================================================================
def _resolve_sources(opts: PipelineOptions, settings: Any) -> tuple[bool, Any, bool]:
    """判定本次运行用到哪条入口，返回 (是否有代码目录, 运行时选项, 是否启用运行时发现)。

    校验规则（宁快速失败，不空跑）：
    - 给了 `local_path` 但它不是目录 → 报错（不静默当作「没有代码」）；
    - 两条入口都没有 → 报错，并给出两个可执行的修法。
    """
    has_code = bool(opts.local_path) and Path(opts.local_path).is_dir()
    if opts.local_path and not has_code:
        raise EngineError(f"被测目录不存在：{Path(opts.local_path)}")
    runtime_options, runtime_enabled = _runtime_target(opts, settings)
    if not has_code and not runtime_enabled:
        raise EngineError(
            "缺少被测来源：请提供被测代码目录（--path / local_path），"
            "或提供被测地址并启用运行时 UI 发现（--url + --runtime-ui / RUNTIME_UI_ENABLED=on）"
        )
    return has_code, runtime_options, runtime_enabled


def run_pipeline(
    opts: PipelineOptions,
    *,
    progress: ProgressFn | None = None,
) -> PipelineResult:
    """执行完整流水线（代码通道 / 地址通道 / 两者并用）。"""
    s = get_settings()
    has_code, runtime_options, runtime_enabled = _resolve_sources(opts, s)

    result = PipelineResult(mode=opts.mode)
    result.source_kind = "+".join(
        [k for k, on in (("code", has_code), ("url", runtime_enabled)) if on]
    )
    stage_register(opts, result)
    files: dict[str, SourceFile] = {}
    if has_code:
        files = stage_scan(opts, result, progress)
        result.functional_points = stage_extract(opts, result, files, progress)
    else:
        result.counts["files"] = 0
        result.counts["functional_points"] = 0
        result.notes.append("未提供被测代码目录：本次只走「测试地址 + 账号密码」通道")
    # P3：运行时 UI 发现（默认关闭）。失败只记错误、不阻断主链路（设计 §10）。
    # M3.4：发现成功后把 UI 功能点**并入静态功能点集合**——必须在 stage_tag 之前，
    # 否则运行时补入的页面不参与测试点展开与用例生成。
    if runtime_enabled:
        try:
            found = stage_runtime_ui(opts, result, progress, runtime_options)
        except EngineError as exc:
            found = None
            result.errors.append(f"运行时 UI 发现失败：{exc.message}")
        if found is not None:
            merged, stats = _merge_runtime_fps(
                result.functional_points, runtime_ui.to_functional_points(found)
            )
            result.functional_points = merged
            result.counts["functional_points"] = len(merged)
            result.counts["runtime_ui_fp_added"] = stats["added"]
            result.counts["runtime_ui_fp_replaced"] = stats["replaced"]
            result.notes.append(
                f"运行时补入 {stats['added']} 条 UI 功能点（覆盖静态同名 {stats['replaced']} 条）"
            )
    _, tag_by_fp = stage_tag(opts, result, result.functional_points, progress)
    tps = stage_test_points(opts, result, result.functional_points, tag_by_fp, progress)
    result.test_points = stage_enrich(opts, result, tps, result.functional_points, progress)
    # P2：PRD 通道（默认关闭）——先解析需求并派生「业务规则」测试点，须在用例生成之前并入。
    if s.prd_enabled and opts.prd_source:
        result.prd_doc = stage_prd_ingest(opts, result, progress)
        _merge_prd_test_points(result)
    result.cases = stage_cases(result, result.test_points, progress)
    if s.llm_design_enabled:
        result.cases = stage_llm_design(opts, result, progress)
    # A3：用例执行（默认关闭）。接口层真实执行；UI 层为桩并会如实标记 skipped。
    if s.executor_enabled or opts.target_req.execute:
        try:
            stage_execute(opts, result, progress, runtime_options)
        except EngineError as exc:
            result.errors.append(f"用例执行失败：{exc.message}")
    stage_persist(opts, result, progress)

    _emit(progress, "done", **result.counts)
    return result


def default_options(local_path: str = "", *, mode: str = "full") -> PipelineOptions:
    """从环境配置构造默认选项（供 API / CLI 使用）。"""
    s = get_settings()
    return PipelineOptions(
        local_path=local_path,
        mode=mode,
        review_status="pending" if s.review_gate else "approved",
        llm=semantic_enrich.EnrichOptions(
            enabled=s.llm_enhance,
            provider=s.llm_provider,
            base_url=s.llm_base_url,
            model=s.llm_model,
            api_key=s.llm_api_key,
            timeout=s.llm_timeout,
        ),
    )


# ============================================================================
# 统一智能输入框：解析结果 → 运行选项（A1）
# ============================================================================
def apply_auto_input(opts: PipelineOptions, parsed: Any) -> list[str]:
    """把智能输入框的解析结果填入运行选项，返回「本次实际采纳的字段名」清单。

    覆盖优先级：**显式 CLI/HTTP 参数 > 智能输入框 > 环境变量**。实现方式：调用方必须
    **先**调本函数、**后**应用显式参数——因此 `mode` / `scopes` 这类有默认值的字段
    允许被输入框覆盖（随后被显式参数再覆盖），而地址/路径只在为空时填充。
    凭证只写入内存中的选项对象，**不写日志、不入产物**。
    """
    adopted: list[str] = []
    if parsed is None:
        return adopted

    def take(field: str, attr: str, *, overwrite: bool = False) -> None:
        value = str(getattr(parsed, field, "") or "")
        if value and (overwrite or not getattr(opts, attr)):
            setattr(opts, attr, value)
            adopted.append(attr)

    take("project_name", "project_name")
    take("mode", "mode", overwrite=True)
    take("base", "base")
    take("target", "target")
    take("local_path", "local_path")
    if parsed.scopes:
        opts.scopes = set(parsed.scopes)
        adopted.append("scopes")

    # 解析结果用的是「目标环境」语义（url → base_url），此处做一次显式字段映射
    req = opts.target_req
    for parsed_field, attr in (
        ("url", "base_url"),
        ("login_url", "login_url"),
        ("user", "login_user"),
        ("password", "login_password"),
        ("otp", "login_otp"),
    ):
        value = str(getattr(parsed, parsed_field, "") or "")
        if value and not getattr(req, attr):
            setattr(req, attr, value)
            adopted.append(f"target.{attr}")
    if parsed.routes and not req.routes:
        req.routes = list(parsed.routes)
        adopted.append("target.routes")
    if req.base_url or req.login_user:
        req.enabled = True  # 给了地址/账号即视为要走地址通道
    return adopted
