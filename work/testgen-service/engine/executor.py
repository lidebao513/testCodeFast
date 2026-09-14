"""引擎 · 模块十一（P3）：用例执行器（接口层探活 / 浏览器交互）。

设计定位：把生成的用例真正跑起来。接口层用例走 `requests` 探活 + 状态断言；
UI 层用例走 Playwright 真实交互。

落库现状（**如实说明，避免跟着文档踩空**）：本模块**只产出执行结论**（内存 +
`PipelineResult.execution` / `counts["exec_*"]`），**不直接写库**；
留痕由 `core.store.record_execution` 在流水线 `stage_persist`（用例对账**之后**）落库——
逐条写 `runs`、回填 `cases.last_result`、并 upsert 批次 `run_batches`（F12，已实现）。
这样分层的原因：执行是运行期活动，落库是存储职责；且必须等用例对账完成、`cases` 行就位后
才能回填 `last_result`，否则首次运行会「无处可写」。

A3 当前范围（本轮交付，见 `两条生成流程_链路梳理与补齐方案.md`）
-----------------------------------------------------------------
- **接口层（`http_probe`）真实执行**：发真实 HTTP 请求，按行为维度判定状态码，
  产出 `pass / fail / error / skipped` 结论与证据；
- **UI 层（`ui_probe`）仍为桩**：返回 `skipped` 并在 note 中**显式说明**「UI 执行器待实现」。
  为什么不假装通过：静默通过会把「没跑」伪装成「跑过了」，比报错危险得多；
- **写操作默认不执行**：POST/PUT/PATCH/DELETE 会改被测环境真实数据，默认 `skipped`；
  确认环境可写后再用 `ExecutorOptions.allow_write` / `EXECUTOR_ALLOW_WRITE=on` 放行。
- **业务函数（`FUNC`）不可直连**：不是 HTTP 接口，如实 `skipped` 并说明需要单测/符号执行。

凭证红线：`auth_token` 只从调用方（环境变量 / 请求级参数）注入，**不进日志、不进结论文本**。
依赖方向严格向下（只 import core）；`requests` 惰性导入。
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.contracts import CaseSpec
from core.enums import HTTP_METHODS, Dimension, ExecStatus, TPType, VerifyLayer
from core.errors import EngineError


# 路径参数（`/invoices/{invoice_id}`）：探测时替换为可请求的占位值
_PATH_PARAM_RE = re.compile(r"\{[^}]+\}")

# 会改变被测环境数据的动词：默认不放行
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# 安全维度可接受的「被拒」状态：401/403 直接拒绝；3xx 通常是跳登录页
_SECURITY_REJECT = frozenset({401, 403})
_SECURITY_REDIRECT = frozenset({301, 302, 303, 307, 308})

# 边界维度可接受的「已校验」状态
_BOUNDARY_OK = frozenset({400, 422})

# 成功码区间（避免裸字面量散落）
_OK_MIN, _OK_MAX = 200, 300
_CLIENT_ERR_MAX = 500


@dataclass
class ExecutorOptions:
    """执行器选项（凭证只在此对象内传递，不落库、不入产物）。"""

    base_url: str = ""
    auth_token: str = ""  # 来自环境变量或请求级参数，不入库
    headless: bool = True  # UI 层预留（本轮未使用）
    timeout: int = 30
    verify_tls: bool = True
    allow_write: bool = False  # 是否放行写操作（默认否：防污染被测环境）
    path_param_value: str = "1"  # 路径参数探测填充值（`{id}` → `1`）


@dataclass
class StepResult:
    """单步执行结果。"""

    seq: int
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"seq": self.seq, "ok": self.ok, "detail": self.detail}


@dataclass
class ExecutionResult:
    """一次用例执行结果。"""

    tc_no: str = ""
    status: str = ExecStatus.SKIPPED.value
    step_results: list[StepResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    duration_ms: int = 0  # 本次执行耗时（毫秒）；落 runs.duration_ms 供报告/趋势使用

    def ok(self) -> bool:
        """是否「已执行且通过」（skipped 不算通过）。"""
        return self.status == ExecStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "tc_no": self.tc_no,
            "status": self.status,
            "ok": self.ok(),
            "step_results": [s.to_dict() for s in self.step_results],
            "notes": self.notes,
            "duration_ms": self.duration_ms,
        }


# ============================================================================
# 判定规则（按行为维度）
# ============================================================================
# 判定「种类」：把「行为维度 × 子维度」归一到 5 类规则之一（表驱动，避免长分支链）
_KIND_NORMAL = "normal"
_KIND_ABNORMAL = "abnormal"
_KIND_AUTH = "auth"
_KIND_PRIV_ESC = "priv_esc"
_KIND_BOUNDARY = "boundary"

_PASS_PREDICATES: dict[str, Callable[[int], bool]] = {
    _KIND_NORMAL: lambda s: _OK_MIN <= s < _OK_MAX,
    _KIND_ABNORMAL: lambda s: _OK_MIN <= s < _CLIENT_ERR_MAX,
    _KIND_AUTH: lambda s: s in _SECURITY_REJECT or s in _SECURITY_REDIRECT,
    _KIND_PRIV_ESC: lambda s: s in _SECURITY_REJECT,
    _KIND_BOUNDARY: lambda s: s in _BOUNDARY_OK,
}

# 种类 → (通过文案, 未通过文案)；状态码由调用方拼接
_VERDICT_DESC: dict[str, tuple[str, str]] = {
    _KIND_NORMAL: ("接口返回成功", "接口未返回成功"),
    _KIND_ABNORMAL: ("异常路径返回 4xx", "异常路径未返回 4xx"),
    _KIND_AUTH: ("无凭证访问被拒", "无凭证访问未被拒绝"),
    _KIND_PRIV_ESC: ("越权访问被拒", "越权访问未被拒绝"),
    _KIND_BOUNDARY: ("非法参数被校验拒绝", "非法参数未被校验"),
}


def _dimension_kind(category: str, dimension: str) -> str:
    """把「行为维度 × 子维度」归一到判定种类。"""
    if category == TPType.SECURITY.value:
        return _KIND_PRIV_ESC if Dimension.PRIV_ESC.value in dimension else _KIND_AUTH
    if category == TPType.BOUNDARY.value:
        return _KIND_BOUNDARY
    if category == TPType.ABNORMAL.value:
        return _KIND_ABNORMAL
    return _KIND_NORMAL


def _judge(category: str, dimension: str, status: int) -> tuple[bool, str]:
    """按行为维度判定是否通过，返回 (是否通过, 人类可读说明)。

    规则与 `tp_expand._expect_of` 的预期文案**逐条对应**——预期写什么就断言什么，
    否则会出现「用例说期望 400、执行器却把 400 判成失败」的自相矛盾。
    """
    kind = _dimension_kind(category, dimension)
    passed = _PASS_PREDICATES[kind](status)
    if passed and kind == _KIND_AUTH and status in _SECURITY_REDIRECT:
        return True, f"无凭证访问被重定向（{status}，疑似跳登录页）"
    return passed, f"{_VERDICT_DESC[kind][0 if passed else 1]}（{status}）"


def _should_attach_auth(category: str, dimension: str) -> bool:
    """是否携带凭证：鉴权缺失维度就是要验证「无凭证被拒」，故**不带**。"""
    return not (category == TPType.SECURITY.value and Dimension.AUTH_MISS.value in dimension)


# ============================================================================
# 请求发送
# ============================================================================
def _new_session() -> Any:
    """建一个 requests 会话（惰性导入；连接复用以减少握手开销）。"""
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - 依赖缺失属部署问题
        raise EngineError("执行接口层用例需要 requests：pip install requests") from exc
    return requests.Session()


def _close_session(session: Any) -> None:
    try:
        session.close()
    except Exception:  # noqa: BLE001 - 关闭失败不影响结论（连接由 OS 回收），无需区分异常类型
        pass


def _materialize_path(path: str, value: str) -> tuple[str, bool]:
    """把路径参数替换为可请求的探测值；返回 (路径, 是否做过替换)。"""
    materialized, count = _PATH_PARAM_RE.subn(value, path)
    return materialized, count > 0


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _send(session: Any, method: str, url: str, options: ExecutorOptions, with_auth: bool) -> Any:
    """发一次请求；凭证以 Authorization 头携带，**绝不放进 URL**。"""
    headers: dict[str, str] = {}
    if with_auth and options.auth_token:
        headers["Authorization"] = f"Bearer {options.auth_token}"
    kwargs: dict[str, Any] = {
        "timeout": options.timeout,
        "verify": options.verify_tls,
        "headers": headers,
        "allow_redirects": False,  # 3xx 是「跳登录」的判据，不能被自动跟随吞掉
    }
    if method in _WRITE_METHODS:
        kwargs["json"] = {}  # 写操作给空体，避免因缺体直接 400 而掩盖真实结论
    return session.request(method, url, **kwargs)


# ============================================================================
# 主入口
# ============================================================================
def execute_case(
    case: CaseSpec,
    options: ExecutorOptions | None = None,
    *,
    session: Any = None,
) -> ExecutionResult:
    """执行单条用例（按 `steps[0].layer` 选择接口 / UI 通道）。

    `session` 可注入（测试用假会话）；为 None 时自建 requests 会话。
    统一在此处测量耗时（落 `runs.duration_ms`），分派逻辑在 `_dispatch`。
    """
    opts = options or ExecutorOptions()
    started = time.monotonic()
    result = _dispatch(case, opts, session)
    result.duration_ms = int((time.monotonic() - started) * 1000)
    return result


def _dispatch(case: CaseSpec, opts: ExecutorOptions, session: Any) -> ExecutionResult:
    """按执行层分派：接口层真发请求，其余如实 skipped（绝不伪装通过）。"""
    step = case.steps[0] if case.steps else {}
    layer = str(step.get("layer") or "")
    if layer != VerifyLayer.INTERFACE.value:
        return _skipped(
            case,
            "UI 层执行器待实现（A3-UI 待做）：本次未执行，**不等于通过**；"
            "请先按 doc_steps 人工执行或用 Playwright 通道复核",
        )
    return _probe_http(case, step, opts, session)


def _skipped(case: CaseSpec, reason: str) -> ExecutionResult:
    """不可执行（UI 层未实现 / 非 HTTP 来源 / 未提供地址 / 写操作未放行）。

    一律带 `StepResult(ok=False)` 与 note 说明**原因**——静默跳过会被误读成通过。
    """
    return ExecutionResult(
        tc_no=case.tc_no,
        status=ExecStatus.SKIPPED.value,
        step_results=[StepResult(seq=3, ok=False, detail=reason)],
        notes=[reason],
    )


def _probe_http(
    case: CaseSpec, step: dict[str, Any], opts: ExecutorOptions, session: Any
) -> ExecutionResult:
    """接口层探活：真实发请求 + 按行为维度断言。"""
    method = str(step.get("method") or "").upper().split(" ")[0]
    path = str(step.get("path") or "")
    if method not in HTTP_METHODS:
        return _skipped(case, "来源非 HTTP 接口（业务函数），接口层无法直连执行 → 需单测/符号执行")
    if not opts.base_url:
        return _skipped(case, "未提供被测地址（--url / RUNTIME_BASE_URL），无法执行接口层用例")
    if not path.startswith("/"):
        return _skipped(case, f"路径不可直接请求：{path!r}（接口层要求以 / 开头）")
    if method in _WRITE_METHODS and not opts.allow_write:
        return _skipped(
            case,
            f"写操作（{method}）默认不执行：会在被测环境产生真实数据变更；"
            "确认环境可写后用 --allow-write 或 EXECUTOR_ALLOW_WRITE=on 放行",
        )

    materialized, substituted = _materialize_path(path, opts.path_param_value)
    url = _join_url(opts.base_url, materialized)
    owns_session = session is None
    active = session or _new_session()
    category = case.case_type
    dimension = str(step.get("dimension") or "")
    try:
        response = _send(active, method, url, opts, _should_attach_auth(category, dimension))
        status_code = int(response.status_code)
    except Exception as exc:  # noqa: BLE001 - 网络/证书/超时/连接被拒等一律转 error 结论，绝不抛给上层
        return ExecutionResult(
            tc_no=case.tc_no,
            status=ExecStatus.ERROR.value,
            step_results=[StepResult(seq=3, ok=False, detail=f"请求失败：{type(exc).__name__}")],
            notes=[f"请求 {method} {materialized} 失败：{type(exc).__name__}"],
        )
    finally:
        if owns_session:
            _close_session(active)

    passed, detail = _judge(category, dimension, status_code)
    notes = [f"{method} {materialized} → {status_code}：{detail}"]
    if substituted:
        notes.append(f"路径参数已用占位值 {opts.path_param_value!r} 探测（真实资源 ID 需人工提供）")
    if category == TPType.SECURITY.value and Dimension.PRIV_ESC.value in dimension:
        notes.append("越权未做资源归属识别，结论置信度较低（见 A3 已知限制）")
    return ExecutionResult(
        tc_no=case.tc_no,
        status=ExecStatus.PASS.value if passed else ExecStatus.FAIL.value,
        step_results=[StepResult(seq=3, ok=passed, detail=detail)],
        notes=notes,
    )


def execute_all(
    cases: list[CaseSpec],
    options: ExecutorOptions | None = None,
) -> dict[str, Any]:
    """批量执行并汇总（单会话复用连接）。"""
    opts = options or ExecutorOptions()
    results: list[ExecutionResult] = []
    session: Any = None
    need_http = any(
        str((c.steps[0] if c.steps else {}).get("layer") or "") == VerifyLayer.INTERFACE.value
        for c in cases
    )
    if need_http:
        session = _new_session()
    try:
        results = [execute_case(case, opts, session=session) for case in cases]
    finally:
        if session is not None:
            _close_session(session)
    return summarize(results)


def summarize(results: list[ExecutionResult]) -> dict[str, Any]:
    """执行结论汇总（供 CLI / HTTP 输出与产物写出）。"""
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    executed = (
        counts.get(ExecStatus.PASS.value, 0)
        + counts.get(ExecStatus.FAIL.value, 0)
        + counts.get(ExecStatus.ERROR.value, 0)
    )
    return {
        "total": len(results),
        "executed": executed,
        "pass": counts.get(ExecStatus.PASS.value, 0),
        "fail": counts.get(ExecStatus.FAIL.value, 0),
        "error": counts.get(ExecStatus.ERROR.value, 0),
        "skipped": counts.get(ExecStatus.SKIPPED.value, 0),
        "status_counts": counts,
        "results": [r.to_dict() for r in results],
    }
