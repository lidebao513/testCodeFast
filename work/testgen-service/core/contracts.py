"""数据契约 v1.0（Single Source of Contract）。

冻结依据：`P1-1_契约冻结说明v1.0.md`。
本模块定义三层产物的**字段、编号算法、八要素、追溯键**，是全服务唯一的契约声明处；
任何产出/消费契约的模块都必须 import 本模块，不得自行拼字段名或自行编号。

三条硬承诺：
  1. 产物可被旧消费方直接读取（字段名/取值域/编号格式一致）
  2. 编号稳定（同一份代码重复跑，编号不变）
  3. 追溯双向且无孤儿
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

from core.enums import FType, Tag, TPType, VerifyLayer


# 契约版本：变更规则见 P1-3《契约升版策略》（只增不破）
CONTRACT_VERSION = "1.0"

# 用例八要素（顺序即展示顺序；缺一不可）
EIGHT_ELEMENTS: tuple[str, ...] = (
    "tc_no",
    "module",
    "title",
    "case_type",
    "priority",
    "precondition",
    "doc_steps",
    "expect",
)

# 优先级：异常/安全/边界 → P1；命中高风险模块 → P1；其余 → P2
HIGH_RISK_MODULE_KEYWORDS: tuple[str, ...] = (
    "鉴权",
    "登录",
    "支付",
    "交易",
    "权限",
    "审批",
)

# 历史别名 → 统一取值（契约缺陷 D-1 的兼容修复）
_TEST_TYPE_ALIASES: dict[str, str] = {
    "新增": Tag.UPDATE.value,
    "更新": Tag.UPDATE.value,
    "全量": Tag.FULL.value,
}


# ============================================================================
# 编号算法（冻结，不可改）
# ============================================================================
def fp_id_of(ftype: str, file_path: str, name: str) -> str:
    """功能点稳定编号：`FP-` + md5(ftype|file_path|name) 前 8 位。

    用哈希而非自增，是为了跨运行、跨机器稳定，且规避路径中的中文/空格/分隔符干扰。
    md5 在此**仅作指纹用途，非安全用途**。
    """
    key = f"{ftype}|{file_path}|{name}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]  # nosec B324  # 非安全用途：仅生成稳定 ID 指纹
    return "FP-" + digest


def tp_id_of(  # noqa: PLR0913, PLR0917 - 编号由多段内容构成，显式列出比包成结构体更清晰
    fp_id: str,
    category: str,
    area: str = "",
    method: str = "",
    dimension: str = "",
    ordinal: int = 0,
) -> str:
    """测试点稳定编号：`TP-` + md5(fp_id|category|area|method|dimension|ordinal) 前 8 位。

    修复契约缺陷 D-2：legacy 用 `TP-{枚举序号}` 是**位置相关**的，文件顺序一变编号全错位。
    本实现把编号绑定到「内容指纹」，同一份代码重复跑编号不变；
    ordinal 用于同一功能点下产生多条同构测试点时的消歧（默认 0）。
    """
    key = f"{fp_id}|{category}|{area}|{method}|{dimension}|{ordinal}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]  # nosec B324  # 非安全用途：仅生成稳定 ID 指纹
    return "TP-" + digest


def normalize_test_type(value: str | None) -> str:
    """把历史标签统一为 `全量` / `更新`（D-1 兼容层：仍接受读出 `新增`）。"""
    if not value:
        return Tag.FULL.value
    return _TEST_TYPE_ALIASES.get(value, Tag.FULL.value)


# ============================================================================
# 三层产物
# ============================================================================
@dataclass
class FunctionalPoint:
    """功能点：从源码提取出的一个「可测行为单元」。"""

    fp_id: str
    ftype: str
    file_path: str
    name: str  # 机器键（如 "POST /api/v1/tasks"），消费方依赖，不可改
    title: str  # 业务化展示名
    module: str = ""
    semantic: str = ""
    description: str = ""
    commit_ref: str = ""
    review_status: str = "approved"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["contract_version"] = CONTRACT_VERSION
        return d


@dataclass
class TestPoint:
    """测试点：功能点展开出的一个「要验证什么」的命题。"""

    # 非 dataclass 字段（无注解）：阻止 pytest 把本类当作测试类采集
    __test__ = False

    tp_id: str
    fp_contract_id: str
    category: str  # 正常 / 异常 / 安全 / 边界
    module: str = ""
    title: str = ""
    semantic: str = ""
    source: str = ""  # 来源文件，统一正斜杠
    method: str = ""
    area: str = ""
    expect: str = ""
    dimension: str = ""
    tag: str = Tag.FULL.value
    review_status: str = "pending"
    verify_layer: str = ""
    # v1.1 预留（只增不改；缺省即 v1.0 语义）
    evidence: list[str] = field(default_factory=list)
    confidence: float = 1.0
    origin: str = "rule"
    unverified: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["contract_version"] = CONTRACT_VERSION
        return d


@dataclass
class CaseSpec:
    """用例规格：测试点落成的「可执行 + 可交付」用例。"""

    tc_no: str
    title: str
    ctype: str  # api / e2e
    steps: list[dict[str, Any]]  # 机器步只在 steps[0]
    module: str = ""
    case_type: str = TPType.NORMAL.value
    priority: str = "P2"
    precondition: str = ""
    doc_steps: list[dict[str, Any]] = field(default_factory=list)
    tp_id: str = ""
    fp_contract_id: str = ""
    fp_row_id: int | None = None
    test_type: str = Tag.FULL.value
    status: str = "generated"
    version: int = 1

    def expect(self) -> str:
        """八要素之「预期结果」：落在 steps[0].expect。"""
        return str(self.steps[0].get("expect", "")) if self.steps else ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["expect"] = self.expect()
        d["contract_version"] = CONTRACT_VERSION
        return d

    def missing_elements(self) -> list[str]:
        """返回缺失的八要素名（空列表 = 八要素齐全）。"""
        mapping: dict[str, Any] = {
            "tc_no": self.tc_no,
            "module": self.module,
            "title": self.title,
            "case_type": self.case_type,
            "priority": self.priority,
            "precondition": self.precondition,
            "doc_steps": self.doc_steps,
            "expect": self.expect(),
        }
        return [k for k in EIGHT_ELEMENTS if not mapping.get(k)]


# ============================================================================
# 派生规则（确定性，不依赖 LLM）
# ============================================================================
def priority_of(category: str, module: str) -> str:
    """优先级规则：异常/安全/边界 → P1；高风险模块 → P1；其余 → P2。"""
    if category in (TPType.ABNORMAL.value, TPType.SECURITY.value, TPType.BOUNDARY.value):
        return "P1"
    if any(k in module for k in HIGH_RISK_MODULE_KEYWORDS):
        return "P1"
    return "P2"


def precondition_of(category: str) -> str:
    """前置条件规则。"""
    if category == TPType.ABNORMAL.value:
        return "被测服务已启动且 base_url 可达；已明确合法/非法输入的构造方式"
    return "被测服务已启动，base_url 可达；涉及鉴权接口需持有有效 token（或测试账号可匿名访问）"


def verify_layer_of_ftype(ftype: str) -> str:
    """按来源类型推导执行层：api/business → 接口；page/ui/component → UI。"""
    if ftype in (FType.API.value, FType.BUSINESS.value):
        return VerifyLayer.INTERFACE.value
    return VerifyLayer.UI.value
