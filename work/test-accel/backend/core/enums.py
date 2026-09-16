"""测试加速平台 · 单一枚举真值源（Single Source of Truth）。

所有「枚举值」（行为维度 / 标签 / 来源类型 / 执行层 / 维度 / 方法标记 / 执行状态 /
拉取状态 / 范围常量）集中定义于此，全项目统一 import 引用，禁止在其它文件硬编码字面量。

设计要点：
- TPType / Tag / FType / VerifyLayer / Dimension 为领域语义枚举；取值（.value）即落库/落盘字符串。
- VerifyLayer 是本次新增的「执行层」维度（UI / 接口），用于选择执行通道；UI 层无法覆盖时
  由 select_execution_mode() 回退到接口层验证。
- MethodMarker / HTTP_METHODS 收纳 method 字段的取值（GET/POST…/PAGE/UI/FUNC），避免散落。
- Scope 常量（ALL_TP_TYPES / DEFAULT_SCOPE / FULL_SCOPE / SCOPE_KEY_ALL）为唯一真值，
  resolve_scope 统一引用，不再在 gen_test_points 重复定义「接口」范围关键词。
"""

from enum import Enum


# ============================ 行为维度（tp_type） ============================
class TPType(Enum):
    """测试点的「行为维度」：测的是哪一种行为特征。与执行层 VerifyLayer 正交。"""

    NORMAL = "正常"  # 功能可用性
    ABNORMAL = "异常"  # 资源/异常态
    SECURITY = "安全"  # 鉴权/越权
    BOUNDARY = "边界"  # 参数/边界


# ============================ 标签（tag） ============================
class Tag(Enum):
    """测试点/用例的增量标签：来自 base..target diff 命中即『更新』。"""

    FULL = "全量"  # 本次完整测试内容（代码未变更部分）
    UPDATE = "更新"  # 本次仅变更/增量测试内容


# ============================ 来源类型（ftype） ============================
class FType(Enum):
    """测试点/功能点的来源类型：来自哪一类代码产物（小写唯一）。"""

    API = "api"  # 后端接口（HTTP 路由）
    PAGE = "page"  # 前端页面路由
    UI = "ui"  # 前端交互组件（method=UI 标记）
    BUSINESS = "business"  # 后端业务函数
    COMPONENT = "component"  # 关键交互组件


# ============================ 执行层（VerifyLayer · 本次新增） ============================
class VerifyLayer(Enum):
    """测试「执行层」维度：决定用例以哪种通道执行。

    - INTERFACE（接口层）：走 HTTP/接口直接验证（requests 探活 + 结构/契约断言）。
    - UI（UI 层）：走真实浏览器渲染交互（Playwright）。
    由 derive_verify_layer(ftype) 给出默认值；用户可在执行时指定 preferred 模式，
    select_execution_mode() 负责 UI→接口回退。
    """

    INTERFACE = "接口"
    UI = "UI"


# 来源类型 → 中文展示名（KIND_DISPLAY，仅展示用）
KIND_DISPLAY = {
    FType.API: "接口",
    FType.PAGE: "页面路由",
    FType.UI: "交互组件",
    FType.BUSINESS: "业务函数",
    FType.COMPONENT: "功能点",
}


# ============================ 维度（dimension 子类） ============================
class Dimension(Enum):
    """tp_type 的细分子维度（用于 expect 文案与归类）。"""

    AVAIL = "正常-可用性"
    AUTH_MISS = "安全-鉴权缺失"
    PRIV_ESC = "安全-越权"
    PARAM_ILLEGAL = "边界-参数缺失/非法"
    RES_NOT_FOUND = "异常-资源不存在"
    BIZ_LOGIC = "业务函数-逻辑可用"
    PAGE_REACH = "页面/路由可达"
    INTERACTIVE = "交互元素可用"


# ============================ 方法标记（method 字段取值） ============================
class MethodMarker(Enum):
    """测试点 method 字段的非 HTTP 标记（前端产物）。HTTP 动词见 HTTP_METHODS。"""

    PAGE = "PAGE"  # 前端页面可达
    UI = "UI"  # 前端交互组件
    FUNC = "FUNC"  # 后端业务函数（非 HTTP）


# HTTP 动词（method 字段的 HTTP 路由取值）：作为规范列表集中维护
HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")
_HTTP_VERB_SET = frozenset(HTTP_METHODS)


# ============================ 执行状态（runs.status） ============================
class ExecStatus(Enum):
    """单条用例执行结论（写 runs.status，并冗余 cases.last_result）。"""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIPPED = "skipped"
    STRUCTURAL_ONLY = "structural_only"  # 仅结构/契约断言，未做真实 HTTP
    BLOCKED_AUTH = "blocked_auth"  # 鉴权缺失被拦截（反向断言命中）
    BLOCKED_REVIEW = "blocked_review"  # 未通过人工审核，跳过
    CANCELLED = "cancelled"  # 执行被中断


# ============================ 用例生命周期状态（cases.status） ============================
class CaseLifecycleStatus(Enum):
    """用例生命周期状态（与执行结论解耦）。"""

    GENERATED = "generated"
    UPDATED = "updated"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"


# ============================ 审核状态（review_status） ============================
class ReviewStatus(Enum):
    APPROVED = "approved"
    PENDING = "pending"


# ============================ 拉取状态（pull） ============================
class PullStatus(Enum):
    """拉取代码的结果状态（与 scripts/pull_code.py::PullStatus 逐值一致）。

    scripts/pull_code.py 为独立脚本（运行时零耦合、不 import backend），其内部
    维护同值本地枚举；两侧一致性由 tests/test_pull_code.py 守护。
    """

    OK = "ok"
    OK_OFFLINE = "ok_offline"  # 离线拉取（跳过远端更新，用本地已有数据）
    CLONE_FAILED = "clone_failed"
    REFS_UNAVAILABLE = "refs_unavailable"  # base/target 任一 ref 不可解析
    REPO_ESCAPE_BLOCKED = "repo_escape_blocked"  # 目录逃逸到祖先仓库，已阻断
    CLONE_REQUIRED_NO_URL = "clone_required_no_url"  # 需克隆但未提供仓库地址
    TARGET_NOT_EMPTY = "target_not_empty"  # 非空且非 git 目录，无法克隆进入


# ============================ 范围常量（Scope · 唯一真值） ============================
# 行为维度全集（顺序即展示顺序）
ALL_TP_TYPES = [t.value for t in TPType]
# 默认范围：正常 + 安全 + 边界 + 异常（与 testgen-service 真值源对齐 · G-14 · 2026-09-16）
# 安全自 2026-09-14 起默认纳入；异常自 2026-09-15 起默认纳入（G-5 修复异常流）。
DEFAULT_SCOPE = {
    TPType.NORMAL.value,
    TPType.SECURITY.value,
    TPType.BOUNDARY.value,
    TPType.ABNORMAL.value,
}
# 全选范围
FULL_SCOPE = set(ALL_TP_TYPES)
# 「全部」同义词（resolve_scope 识别为全选，不注册为枚举值）
SCOPE_KEY_ALL = ("全部", "所有", "全量", "完整", "all", "ALL")


# ============================ 工具函数 ============================
def derive_verify_layer(ftype: str) -> VerifyLayer:
    """由来源类型推导默认执行层。

    - api / business → 接口层（无 UI 面，直接 HTTP/函数验证）
    - page / ui / component → UI 层（前端产物，优先浏览器渲染）
    """
    if ftype in (FType.API.value, FType.BUSINESS.value):
        return VerifyLayer.INTERFACE
    return VerifyLayer.UI


def select_execution_mode(preferred: VerifyLayer, ftype: str, ui_available: bool) -> VerifyLayer:
    """按用户所选模式 + 测试点特征，决定实际执行层（含 UI→接口回退）。

    - 选接口层：直接走接口层，无回退。
    - 选 UI 层：
        * 测试点本质是接口型（api/business）→ 回退接口层（无 UI 面可覆盖）；
        * 或 UI 执行环境不可用（无浏览器/Playwright）→ 回退接口层；
        * 否则正常走 UI 层。
    返回实际采用的执行层；调用方据此设置 layer_fallback 标记。
    """
    if preferred == VerifyLayer.INTERFACE:
        return VerifyLayer.INTERFACE
    if ftype in (FType.API.value, FType.BUSINESS.value) or not ui_available:
        return VerifyLayer.INTERFACE
    return VerifyLayer.UI


def verify_layer_of(tp: dict, default_ftype: str | None = None) -> VerifyLayer:
    """从测试点取执行层：优先用已注入的 verify_layer 字段，否则按 ftype 推导。"""
    vl = tp.get("verify_layer")
    if vl in (VerifyLayer.INTERFACE.value, VerifyLayer.UI.value):
        return VerifyLayer(vl)
    ftype = tp.get("ftype") or default_ftype
    if not ftype:
        # 退而从 method 推导 ftype
        m = (tp.get("method") or "").upper().split()[0] if tp.get("method") else ""
        if m in _HTTP_VERB_SET:
            ftype = FType.API.value
        elif m == MethodMarker.PAGE.value:
            ftype = FType.PAGE.value
        elif m == MethodMarker.UI.value:
            ftype = FType.UI.value
        else:
            ftype = FType.BUSINESS.value
    return derive_verify_layer(ftype)


def method_kind(method: str):
    """由 method 字段推导来源种类（兼容 _kind_of 旧语义）。

    返回 api / page / ui / business（business 含 FUNC 与其它）。
    """
    m = (method or "").strip().upper()
    verb = m.split()[0] if m else ""
    if verb in _HTTP_VERB_SET:
        return FType.API.value
    if verb == MethodMarker.PAGE.value:
        return FType.PAGE.value
    if verb == MethodMarker.UI.value:
        return FType.UI.value
    return FType.BUSINESS.value


def is_http_method(method: str) -> bool:
    """method 是否为 HTTP 动词。"""
    m = (method or "").strip().upper().split()[0] if method else ""
    return m in _HTTP_VERB_SET
