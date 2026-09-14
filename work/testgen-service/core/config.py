"""集中配置：全部来自环境变量，并在启动时**集中校验、快速失败**。

规则：
- 密钥只允许出现在 `.env` / 环境变量中，**绝不硬编码**、绝不写日志；
- 非法值（如 PORT 非数字）在启动期即抛 `ConfigError`，不拖到运行期炸；
- 只提交 `.env.example`（占位值），真实 `.env` 由 `.gitignore` 排除。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from core.enums import (
    BUSINESS_EXTRACT_CHOICES,
    BUSINESS_EXTRACT_STRICT,
    LAYER_STRATEGY_CHOICES,
)
from core.errors import ConfigError


# 项目根（core/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """尽力加载 .env；python-dotenv 缺失时静默跳过（不阻断启动）。"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _as_bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on", "y", "t")


def _as_int(raw: str | None, default: int, name: str) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"环境变量 {name} 必须是整数，实际为 {raw!r}") from exc


def _as_choice(raw: str | None, default: str, name: str, allowed: tuple[str, ...]) -> str:
    val = (raw or default).strip().lower()
    if val not in allowed:
        raise ConfigError(f"环境变量 {name} 取值非法：{val!r}，允许 {allowed}")
    return val


def _split_list(raw: str | None, default: list[str]) -> list[str]:
    """将逗号分隔的环境变量解析为去空白、去空字符串的列表。"""
    if not raw:
        return list(default)
    return [p.strip() for p in raw.split(",") if p.strip()]


@dataclass
class Settings:
    """运行时配置快照（启动时构造一次）。"""

    app_env: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8100

    log_level: str = "INFO"
    log_format: str = "json"

    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    output_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "outputs")
    db_path: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "testgen.db")
    workspace_root: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "workspaces")

    # 只读工作区：落盘后是否强制置只读（chmod）
    readonly_strict: bool = True

    # 审核门：开启后新产出的功能点/测试点 review_status=pending
    review_gate: bool = False

    # 覆盖层策略（UI 优先）：ui_first=UI 为主、接口仅补充；all=两层独立全量（旧行为）
    layer_strategy: str = "ui_first"
    # ui_first 下是否直接丢弃「接口补充」用例（默认保留并标记 supplement，便于回退）
    drop_supplement_cases: bool = False

    # LLM 增强通道（默认关闭：规则引擎必须先能独立跑通）
    llm_enhance: bool = False
    llm_provider: str = "qwen"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    llm_timeout: int = 60

    # 业务函数提取模式（P1 · 收窄）：strict=排除测试/脚手架/构建脚本/配置模式类文件中的
    # 业务函数；loose=保留全部（legacy 行为）。详见 qa-test-points 技能 §十四。
    business_extract_mode: str = BUSINESS_EXTRACT_STRICT
    # strict 模式下仍保留为独立业务能力的目录白名单（相对仓库根，env 逗号分隔覆盖）。
    # 这些目录被显式认定为「独立能力来源」（工具/智能体/MCP 服务/技能）。
    business_include_dirs: list[str] = field(
        default_factory=lambda: ["tools", "agents", "mcp_servers", "workspace/skills"]
    )

    # 鉴权：为空表示不校验（仅限内网/开发）
    auth_token: str = ""

    def public_dict(self) -> dict[str, object]:
        """可安全输出的配置摘要（**不含密钥**）。"""
        return {
            "app_env": self.app_env,
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "db_path": str(self.db_path),
            "output_dir": str(self.output_dir),
            "workspace_root": str(self.workspace_root),
            "readonly_strict": self.readonly_strict,
            "review_gate": self.review_gate,
            "layer_strategy": self.layer_strategy,
            "drop_supplement_cases": self.drop_supplement_cases,
            "llm_enhance": self.llm_enhance,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_key_configured": bool(self.llm_api_key),
            "auth_enabled": bool(self.auth_token),
            "business_extract_mode": self.business_extract_mode,
            "business_include_dirs": self.business_include_dirs,
        }

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.output_dir, self.workspace_root):
            d.mkdir(parents=True, exist_ok=True)


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """从环境变量构造 Settings；非法即抛 ConfigError。"""
    if env is None:
        _load_dotenv()
        env = dict(os.environ)

    def g(key: str) -> str | None:
        return env.get(key)

    s = Settings(
        app_env=_as_choice(g("APP_ENV"), "dev", "APP_ENV", ("dev", "test", "prod")),
        host=g("HOST") or "127.0.0.1",
        port=_as_int(g("PORT"), 8100, "PORT"),
        log_level=(g("LOG_LEVEL") or "INFO").upper(),
        log_format=_as_choice(g("LOG_FORMAT"), "json", "LOG_FORMAT", ("json", "text")),
        readonly_strict=_as_bool(g("READONLY_STRICT"), True),
        review_gate=_as_bool(g("REVIEW_GATE"), False),
        layer_strategy=_as_choice(
            g("LAYER_STRATEGY"), "ui_first", "LAYER_STRATEGY", LAYER_STRATEGY_CHOICES
        ),
        drop_supplement_cases=_as_bool(g("DROP_SUPPLEMENT_CASES"), False),
        llm_enhance=_as_bool(g("LLM_ENHANCE"), False),
        llm_provider=(g("LLM_PROVIDER") or "qwen").strip().lower(),
        llm_base_url=g("LLM_BASE_URL") or "",
        llm_model=g("LLM_MODEL") or "",
        llm_api_key=g("LLM_API_KEY") or "",
        llm_timeout=_as_int(g("LLM_TIMEOUT"), 60, "LLM_TIMEOUT"),
        auth_token=g("AUTH_TOKEN") or "",
        business_extract_mode=_as_choice(
            g("BUSINESS_EXTRACT_MODE"),
            BUSINESS_EXTRACT_STRICT,
            "BUSINESS_EXTRACT_MODE",
            BUSINESS_EXTRACT_CHOICES,
        ),
        business_include_dirs=_split_list(
            g("BUSINESS_INCLUDE_DIRS"),
            ["tools", "agents", "mcp_servers", "workspace/skills"],
        ),
    )

    if g("DATA_DIR"):
        s.data_dir = Path(g("DATA_DIR") or "").expanduser().resolve()
    if g("OUTPUT_DIR"):
        s.output_dir = Path(g("OUTPUT_DIR") or "").expanduser().resolve()
    if g("WORKSPACE_ROOT"):
        s.workspace_root = Path(g("WORKSPACE_ROOT") or "").expanduser().resolve()
    db_path_env = g("DB_PATH")
    s.db_path = (
        Path(db_path_env).expanduser().resolve() if db_path_env else s.data_dir / "testgen.db"
    )

    if s.llm_enhance and not s.llm_api_key:
        raise ConfigError("LLM_ENHANCE=on 时必须提供 LLM_API_KEY")
    if s.port <= 0 or s.port > 65535:
        raise ConfigError(f"PORT 越界：{s.port}")

    return s


_settings: Settings | None = None


def get_settings() -> Settings:
    """进程内单例（首次调用即校验）。"""
    global _settings
    if _settings is None:
        _settings = load_settings()
        _settings.ensure_dirs()
    return _settings


def reset_settings() -> None:
    """测试用：清空单例。"""
    global _settings
    _settings = None
