"""引擎 · 编排（pipeline）：把六个模块串成一条可复现的流水线。

    扫描 → 功能点提取 → 差异打标 → 测试点展开 → 语义增强 → 用例生成 → 落库

设计要点：
- **每个阶段一个函数**：输入输出都是显式数据，便于单测与影子双跑比对；
- **全量 / 增量同一条链路**，差异只体现在「是否传入 diff 上下文」；
- 任一阶段失败都带上下文抛出（`EngineError`），不吞异常。
- **可选扩展阶段（P2/P3）默认关闭**：由 Settings 的 flag 守卫；其中 P3 运行时
  UI 发现失败**只记错误不阻断主链路**（见 `P3_UI生成_详细设计.md` §10）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
class PipelineOptions:
    """一次运行的完整输入。"""

    local_path: str
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

    @property
    def is_incremental(self) -> bool:
        return self.mode == "incremental"


@dataclass
class PipelineResult:
    """一次运行的结果摘要（可序列化，供 API / CLI 输出）。"""

    project_id: int | None = None
    mode: str = "full"
    counts: dict[str, int] = field(default_factory=dict)
    scope_summary: dict[str, int] = field(default_factory=dict)
    tag_summary: dict[str, int] = field(default_factory=dict)
    case_stats: dict[str, Any] = field(default_factory=dict)
    traceability: dict[str, Any] = field(default_factory=dict)
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
            "counts": self.counts,
            "scope_summary": self.scope_summary,
            "tag_summary": self.tag_summary,
            "case_stats": self.case_stats,
            "traceability": self.traceability,
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
def stage_register(opts: PipelineOptions, result: PipelineResult) -> None:
    if opts.persist:
        init_db()
        name = opts.project_name or Path(opts.local_path).name
        result.project_id = store.upsert_project(name, str(opts.local_path))
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


def stage_runtime_ui(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
) -> Any | None:
    """P3：运行时浏览器 UI 发现（真实实现，里程碑 M3.1–M3.2）。

    用 Playwright 打开被测环境、以账号密码登录、遍历路由抓取真实可交互元素，
    结果挂到 `result.runtime_ui` 并计入 counts。

    **本阶段只负责「发现」**：把发现的 UI 功能点并入功能点集合并参与测试点展开
    属 M3.4（合并去重 + 增量标「全量」），requests 降级属 M3.5。
    凭证经 `.env` 注入，不落库、不入产物。
    """
    s = get_settings()
    _emit(progress, "runtime_ui", base_url=s.runtime_base_url)
    if not s.runtime_base_url:
        result.notes.append("运行时 UI 发现已跳过：未配置 RUNTIME_BASE_URL")
        return None
    found = runtime_ui.discover_ui(
        runtime_ui.options_from_settings(s),
        static_paths=_static_page_paths(result.functional_points),
    )
    result.runtime_ui = found
    result.notes.extend(f"运行时 UI：{n}" for n in found.notes)
    result.notes.append("运行时 UI 功能点尚未并入主链路（待 M3.4 合并去重）")
    result.counts["runtime_ui_pages"] = len(found.pages)
    result.counts["runtime_ui_reachable"] = sum(1 for p in found.pages if p.reachable)
    result.counts["runtime_ui_elements"] = len(found.elements)
    return found


def stage_execute(
    opts: PipelineOptions,
    result: PipelineResult,
    progress: ProgressFn | None,
) -> Any | None:
    """P3 接入点：执行生成的用例（当前为骨架，返回 None）。

    后续实现由 executor.execute_case 分派 requests / Playwright；
    执行结果回填 cases.last_result 与 runs。启用 executor_enabled 即触发本钩子。
    """
    _emit(progress, "execute", enabled=True)
    return None


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
    cases = case_gen.generate_cases(
        tps,
        ui_modules=ui_modules,
        strategy=s.layer_strategy,
        drop_supplement=s.drop_supplement_cases,
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
def run_pipeline(
    opts: PipelineOptions,
    *,
    progress: ProgressFn | None = None,
) -> PipelineResult:
    """执行完整流水线。"""
    local = Path(opts.local_path)
    if not local.is_dir():
        raise EngineError(f"被测目录不存在：{local}")

    s = get_settings()
    result = PipelineResult(mode=opts.mode)
    stage_register(opts, result)
    files = stage_scan(opts, result, progress)
    result.functional_points = stage_extract(opts, result, files, progress)
    # P3：运行时 UI 发现（默认关闭）。失败只记错误、不阻断主链路（设计 §10）。
    if s.runtime_ui_enabled:
        try:
            stage_runtime_ui(opts, result, progress)
        except EngineError as exc:
            result.errors.append(f"运行时 UI 发现失败：{exc.message}")
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
    if s.executor_enabled:
        result.notes.append("executor 接入点已触发（P3 骨架未实现，execute_case 待落地）")
        stage_execute(opts, result, progress)
    stage_persist(opts, result, progress)

    _emit(progress, "done", **result.counts)
    return result


def default_options(local_path: str, *, mode: str = "full") -> PipelineOptions:
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
