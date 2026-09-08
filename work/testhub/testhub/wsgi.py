"""WSGI 入口（传统部署用；实时通道走 asgi）。"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testhub.settings")
application = get_wsgi_application()
