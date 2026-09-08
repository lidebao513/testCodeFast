"""testhub 项目配置。

合并"测试加速平台"后的关键约定（详见 MIGRATION.md）：
- 后端 Daphne(:8000) 承载 ASGI；Celery 跑长任务；Channels 走实时进度。
- DB 默认 MySQL 8.0；设 DB_ENGINE=sqlite3 可平迁开发。
- LLM 凭据入库（requirement_analysis.AIModelConfig），.env 仅留基础设施密钥。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# 业务 app 统一放在 apps/ 下
sys_path = str(BASE_DIR / "apps")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "corsheaders",
    "channels",
    # testhub 既有 app（复用）
    "apps.users",
    "apps.projects",
    "apps.testcases",
    "apps.reports",
    "apps.reviews",
    "apps.requirement_analysis",
    "apps.ui_automation",
    "apps.executions",
    "apps.core",
    "apps.monitor",
    # === 合并"测试加速平台"必须新建的三个 app（§11.3）===
    "apps.code_analysis",       # AST 功能点抽取 + change_log 增量溯源
    "apps.accel_skills",        # Skill 资产库（平台独有核心资产）
    "apps.deployment_target",   # 被测目标：只读克隆 + 端口池 + 进程托管 + 探活
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "testhub.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "testhub.wsgi.application"
ASGI_APPLICATION = "testhub.asgi.application"

# ---------- 数据库：MySQL 8.0 默认，DB_ENGINE=sqlite3 平迁 ----------
DB_ENGINE = os.getenv("DB_ENGINE", "mysql")
if DB_ENGINE == "sqlite3":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "data" / "testhub.db")),
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "testhub"),
        "USER": os.getenv("DB_USER", "testhub"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }}

CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
}}

# ---------- Celery（长任务 + 增量回归 beat）----------
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/2")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/3")
CELERY_TIMEZONE = "Asia/Shanghai"

# ---------- DRF / CORS ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
CORS_ALLOW_ALL_ORIGINS = True

# ---------- 被测目标服务端口池（deployment_target 管理，§11.3）----------
DEPLOY_PORT_POOL = [p for p in range(8100, 8200)]  # 可用端口区间

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
