"""平台配置：从 .env 加载，所有密钥不进代码/不进 git。"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # test-accel/
DATA_DIR = PROJECT_ROOT / "data"

load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    # 平台
    PLATFORM_PORT = int(os.getenv("PLATFORM_PORT", "8000"))

    # LLM（默认 Qwen）
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen")
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # 功能点提取：读代码结构为主；LLM 仅作可选增强
    LLM_ENHANCE = os.getenv("LLM_ENHANCE", "on").lower() == "on"
    # 人工审查门：默认开启；关闭则全链路自动到终态
    REVIEW_GATE = os.getenv("REVIEW_GATE", "on").lower() == "on"

    # 动态 HTTP 探测：默认关闭。最小闭环只做静态断言；被测服务起好后再开。
    # 开启后执行器对每个项目仅做一次 /health 探活（缓存），避免逐 case 超时阻塞。
    ENABLE_DYNAMIC_PROBE = os.getenv("ENABLE_DYNAMIC_PROBE", "off").lower() == "on"

    # —— 用例:测试点 映射策略（可配置）——
    # CASE_PER_TP = "one"    ：1 个测试点 → 1 条用例（默认，向后兼容，测试点数 == 用例数）
    # CASE_PER_TP = "split"  ：1 个测试点 → 按维度拆多条用例（测试点数 < 用例数）
    # CASE_PER_TP = "merge"  ：多个同功能点测试点 → 合并为 1 条用例（测试点数 > 用例数）
    CASE_PER_TP = os.getenv("CASE_PER_TP", "one").lower()
    # split 模式：拆分维度。逗号分隔，仅对命中这些维度的测试点拆多条；
    # 默认 "正常,边界,异常,安全"（即按 4 大维度各一条）。留空则按测试点自带的
    # dimension 拆（更细，但数量不可控）。
    CASE_SPLIT_DIMENSIONS = os.getenv("CASE_SPLIT_DIMENSIONS", "正常,边界,异常,安全")

    # —— 阶段4 批次3 ——
    # D-②1 鉴权态复用：执行前自动取 token 并注入 Authorization 头。
    # 凭据**只允许**来自环境变量或 projects.auth_config，禁止硬编码进代码（D-②8）。
    AUTH_AUTO_LOGIN = os.getenv("AUTH_AUTO_LOGIN", "on").lower() == "on"
    RA_ACCOUNT = os.getenv("RA_ACCOUNT", "")
    RA_PASSWORD = os.getenv("RA_PASSWORD", "")
    RA_OTP = os.getenv("RA_OTP", "")
    # 已有可用 token 时直接复用，跳过登录（如统一身份/SSO 场景）
    RA_AUTH_TOKEN = os.getenv("RA_AUTH_TOKEN", "")
    # 可选：覆盖默认登录端点（默认 /api/v1/auth/unified-login，回退 /api/v1/auth/login）
    RA_LOGIN_PATH = os.getenv("RA_LOGIN_PATH", "/api/v1/auth/unified-login")
    RA_LOGIN_FALLBACK_PATH = os.getenv("RA_LOGIN_FALLBACK_PATH", "/api/v1/auth/login")
    # token 缓存时长（秒），避免每条用例都登录
    AUTH_TOKEN_TTL = int(os.getenv("AUTH_TOKEN_TTL", "1800"))

    # D-②2 并发执行：IO 密集型（HTTP 探活）用线程池；写库仍串行，规避 SQLite 写锁
    EXEC_MAX_WORKERS = int(os.getenv("EXEC_MAX_WORKERS", "4"))

    # —— 阶段4 批次4 ——
    # D-★3 真实浏览器：可选依赖，未安装/不可用则优雅降级为静态断言
    ENABLE_BROWSER = os.getenv("ENABLE_BROWSER", "off").lower() == "on"
    # 前端地址（page 类用例真实渲染用）；留空则回退 base_url
    RA_FRONTEND_URL = os.getenv("RA_FRONTEND_URL", "")
    BROWSER_TIMEOUT_MS = int(os.getenv("BROWSER_TIMEOUT_MS", "15000"))
    BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "on").lower() == "on"
    # 留空则用 playwright 自带 chromium；也可指向本机 Chrome（exec_live.py 的用法）
    BROWSER_EXECUTABLE_PATH = os.getenv("BROWSER_EXECUTABLE_PATH", "")
    # 启动/单次操作的硬超时（秒）：沙箱里 chromium 可能挂起，超时即降级为静态断言
    BROWSER_LAUNCH_TIMEOUT = int(os.getenv("BROWSER_LAUNCH_TIMEOUT", "60"))
    # 截图策略：always = 成功也截图（慢）；on_fail = 仅失败截图（默认）
    SCREENSHOT_POLICY = os.getenv("SCREENSHOT_POLICY", "on_fail").lower()

    # 数据目录
    DB_PATH = DATA_DIR / "test_accel.db"
    SKILLS_DIR = DATA_DIR / "skills"
    REPORTS_DIR = DATA_DIR / "reports"
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    LOGS_DIR = DATA_DIR / "logs"

    def ensure_dirs(self):
        for d in (DATA_DIR, self.SKILLS_DIR, self.REPORTS_DIR, self.SCREENSHOTS_DIR, self.LOGS_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
