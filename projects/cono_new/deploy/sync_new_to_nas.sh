#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="cono-nas"
DEST="/volume1/docker/cono_app"

echo "==> 构建前端 ..."
cd "$ROOT/frontend" && npm run build

echo "==> 上传新版后端（不含 venv/node_modules）..."
rsync -az --delete --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude 'db.sqlite3' "$ROOT/api/" "$HOST:$DEST/api/"

echo "==> 上传前端产物 ..."
rsync -az --delete "$ROOT/frontend/dist/" "$HOST:$DEST/frontend/dist/"

echo "==> 上传部署配置 ..."
rsync -az "$ROOT/deploy/" "$HOST:$DEST/deploy/"

echo "==> 重启新版容器 ..."
ssh "$HOST" "sudo docker compose -f $DEST/deploy/docker-compose.new.yml up -d --build"

echo "==> 校验 ..."
sleep 6
curl -s -o /dev/null -w "新版前端: %{http_code}\n" http://192.168.1.202:8001/
curl -s -o /dev/null -w "老版: %{http_code}\n" http://192.168.1.202:8000/
echo "==> 新版上线完成 http://192.168.1.202:8001/"
