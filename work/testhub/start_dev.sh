#!/usr/bin/env bash
# testhub 开发启动脚本（§11.8 / §11.6）
# 顺序：DB 迁移 → Daphne(:8000) → Celery worker+beat → 前端(:3000)
set -e
cd "$(dirname "$0")"

# 1) 依赖（首次）
# python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
# cd frontend && npm install && npm run build && cd ..

# 2) 数据库迁移（含新建三 app：code_analysis / accel_skills / deployment_target）
python manage.py migrate

# 3) 后端 ASGI（Daphne :8000）
daphne -b 0.0.0.0 -p 8000 testhub.asgi:application &
DAPI=$!

# 4) Celery：worker（长任务）+ beat（增量回归调度）
celery -A testhub worker -l info &
CELW=$!
celery -A testhub beat -l info &
CELB=$!

# 5) 前端（Vue3 :3000，或 serve 已 build 的 dist）
# (cd frontend && npm run dev -- --port 3000) &

echo "testhub dev up: API :8000 | frontend :3000"
wait $DAPI $CELW $CELB
