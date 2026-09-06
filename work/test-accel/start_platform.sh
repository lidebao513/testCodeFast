#!/usr/bin/env bash
# 测试加速平台启动脚本
# 固化：清理系统 HTTP 代理，避免平台内 requests（冒烟/探活）把 localhost 请求转发到代理导致 502/超时。
cd "$(dirname "$0")" || exit 1
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy NO_PROXY
for p in $(netstat -ano 2>/dev/null | grep ':8000' | grep LISTENING | awk '{print $5}'); do
  taskkill /F /PID "$p" 2>/dev/null
done
sleep 1
exec ./venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
