"""平台配置：从 .env 加载，所有密钥不进代码/不进 git。"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent          # backend/
PROJECT_ROOT = BASE_DIR.parent                      # test-accel/
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
