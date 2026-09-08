"""ASGI 入口（Daphne / Channels 实时进度用）。"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testhub.settings")
application = get_asgi_application()
