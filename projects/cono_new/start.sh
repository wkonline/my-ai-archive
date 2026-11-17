#!/bin/bash
# 启动前后端服务
set -e

echo "启动后端服务 (gunicorn)..."
cd /Users/wkonline/MyAI/projects/cono_new/api
nohup /Users/wkonline/MyAI/projects/cono_new/.venv/bin/python -m gunicorn cono_api.wsgi:application \
    --bind 127.0.0.1:8001 --workers 1 --timeout 120 \
    > /tmp/gunicorn.log 2>&1 &
echo "后端 PID: $!"

echo "启动前端服务 (vite)..."
cd /Users/wkonline/MyAI/projects/cono_new/frontend
nohup node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 \
    > /tmp/vite.log 2>&1 &
echo "前端 PID: $!"

sleep 4
echo ""
echo "=== 状态检查 ==="
lsof -i :5173 | head -2
lsof -i :8001 | head -2
echo ""
echo "前端: http://localhost:5173/"
echo "后端: http://localhost:8001/"
echo "登录: admin / admin123"
