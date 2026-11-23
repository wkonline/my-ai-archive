#!/bin/bash
# 新版前后端分离系统 · 部署到 NAS（192.168.1.202）
#
# 线上架构（全部 host 网络）：
#   8001  cono_web_new(Nginx)  静态前端 + /api/ 反代到 127.0.0.1:8002
#   8002  cono_api(Gunicorn)   新版 DRF 后端，代码通过 bind mount 挂载
#                              (/volume1/docker/cono_app -> /app，工作目录 /app/api)
#   8000  cono_web             老版系统，本脚本不触碰
#
# 部署策略：整仓同步 → 重建 API 镜像（含 pip 依赖）→ 重建 API 容器
#           → 执行数据库迁移 → 重载 Nginx → 校验。
#   * 新版后端依赖仓库根目录的 cono/（复用老版模型）和 cono_new/settings.py
#     （CONO_PERMISSION / CONO_MENU），所以必须整仓同步，不能只传 api/。
#   * 后端代码是 bind mount，但 Python 依赖烤在镜像里，requirements.txt 变化
#     必须重建镜像；且 docker restart 不会切换镜像，必须删除容器后重建。
#   * 镜像层顺序是 COPY requirements.txt → pip install → COPY . .，
#     代码改动不会让 pip 层失效，日常同步重建很快。
#   * NAS 上的 /usr/bin/rsync 是群晖 setuid 特制版，不支持 --server 模式
#     （报 "rsync service is no running"），所以这里用 tar over ssh，
#     与 sync_to_nas.sh 保持一致。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="cono-nas"
DEST="/volume1/docker/cono_app"
DOCKER="/var/packages/ContainerManager/target/usr/bin/docker"
SSH_OPTS=(-o BatchMode=yes -o ControlMaster=no -o ControlPath=none -o StrictHostKeyChecking=accept-new)

# 排除本地/运行时产物。注意：NAS 上的 media、backups 是独立挂载目录，覆盖会丢数据；
# frontend/dist 单独同步，避免同步过程中把正在使用的产物删掉。
EXCLUDES=(
  --exclude='.git'
  --exclude='.venv'
  --exclude='node_modules'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='.DS_Store'
  --exclude='._*'
  --exclude='.idea'
  --exclude='.vscode'
  --exclude='.chrome-profile'
  --exclude='.vite'
  --exclude='db.sqlite3'
  --exclude='media'
  --exclude='staticfiles'
  --exclude='backups'
  --exclude='frontend/dist'
)

# 仅当 src/ 有变更时才重建前端；否则直接跳过以节省时间
echo "==> 1/7 重新构建前端 ..."
cd "$ROOT/frontend"
npm run build

echo "==> 2/7 整仓同步到 $HOST:$DEST ..."
COPYFILE_DISABLE=1 tar -czf - "${EXCLUDES[@]}" -C "$ROOT" . \
  | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C $DEST"

echo "==> 3/7 同步前端产物（原地覆盖 + 清理旧 hash 文件）..."
# 必须原地覆盖：nginx 容器的 /usr/share/nginx/html 是 bind mount，
# 一旦把 dist 目录整体换掉（mv 成新 inode），容器里的挂载仍指向已删除的旧目录，会 403。
COPYFILE_DISABLE=1 tar -czf - -C "$ROOT/frontend/dist" . \
  | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C $DEST/frontend/dist"

tmp_remote=$(mktemp); tmp_local=$(mktemp); tmp_del=$(mktemp)
ssh "${SSH_OPTS[@]}" "$HOST" "cd $DEST/frontend/dist && find . -type f" \
  | sed 's|^\./||' | LC_ALL=C sort > "$tmp_remote"
( cd "$ROOT/frontend/dist" && find . -type f | sed 's|^\./||' | LC_ALL=C sort ) > "$tmp_local"
LC_ALL=C comm -23 "$tmp_remote" "$tmp_local" > "$tmp_del"
if [ -s "$tmp_del" ]; then
  { echo "cd '$DEST/frontend/dist'"; sed 's|^|rm -f -- "|; s|$|"|' "$tmp_del"; } \
    | ssh "${SSH_OPTS[@]}" "$HOST" "bash -s"
  echo "    清理旧文件 $(wc -l < "$tmp_del" | tr -d ' ') 个"
fi
rm -f "$tmp_remote" "$tmp_local" "$tmp_del"

echo "==> 4/7 重建新版 API 镜像（同步 pip 依赖）..."
ssh "${SSH_OPTS[@]}" "$HOST" "cd $DEST/api && sudo -n $DOCKER build -q -t cono_api:latest . >/tmp/cono_api_build.log 2>&1 && echo '    镜像已更新' || { echo '!! 镜像构建失败，容器保持原状'; tail -20 /tmp/cono_api_build.log; exit 1; }"

echo "==> 5/7 重建新版 API 容器 ..."
# restart 不会切换到新镜像，必须 rm + run；-w /app/api 让 cono_api 包可导入。
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER rm -f cono_api >/dev/null 2>&1 || true; \
  sudo -n $DOCKER run -d --name cono_api --restart unless-stopped --network host \
    -w /app/api \
    -e DJANGO_SECRET_KEY=nas-cono-new-api-key-2026 \
    -e DJANGO_DEBUG=false \
    -e USE_MYSQL=1 \
    -e DJANGO_DB_NAME=cono \
    -e DJANGO_DB_USER=cono \
    -e DJANGO_DB_PASSWORD=cono2024 \
    -e DJANGO_DB_HOST=192.168.1.201 \
    -e DJANGO_DB_PORT=3306 \
    -v /volume1/docker/cono_app:/app \
    -v /volume1/docker/cono_media:/app/media \
    -v /volume1/docker/cono_backups:/app/backups \
    cono_api:latest gunicorn cono_api.wsgi:application --bind 0.0.0.0:8002 --workers 2 --timeout 120 >/dev/null && \
  sudo -n $DOCKER ps --filter name=cono_api --format '    {{.Names}}  {{.Status}}'"

echo "==> 6/7 执行数据库迁移 ..."
# 代码是 bind mount，第 5 步一重建容器新代码就生效，但表结构还没跟上；
# 少了这一步，新增迁移对应的页面会 500（例如 0044 的客户联系人）。
# 走 cono_api（工作目录 /app/api，PyMySQL），与备份命令同一条路径。
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_api python manage.py migrate --noinput 2>&1 | tail -5"

# nginx 配置/前端产物变化后重载（不重启容器）
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web_new nginx -t >/dev/null 2>&1 && sudo -n $DOCKER exec cono_web_new nginx -s reload >/dev/null 2>&1 && echo '    Nginx 已重载'"

# 备份容器：每天 23:00 自动备份数据库，保留 60 天
# 必须走 api/manage.py（cono_api.settings 用 PyMySQL 充当 MySQLdb）；cono_api 镜像里
# 没有 mysqlclient，跑根目录 manage.py（cono_new.settings）会直接 ImproperlyConfigured。
# 早期部署创建的 cono_backup 用的是旧命令，会静默失败，这里检测到不一致就重建。
BACKUP_CMD='python api/manage.py backup_database --if-due --retention-days 60'
backup_cmd=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER inspect -f '{{join .Config.Cmd \" \"}}' cono_backup 2>/dev/null" || true)
if [ -n "$backup_cmd" ] && [[ "$backup_cmd" != *"api/manage.py"* ]]; then
    echo "==> cono_backup 命令已过期，重建 ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER rm -f cono_backup >/dev/null 2>&1 || true"
    backup_cmd=""
fi
if [ -n "$backup_cmd" ]; then
    echo "==> cono_backup 已存在"
else
    echo "==> 创建定时备份容器 cono_backup ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER run -d --name cono_backup \
        --restart unless-stopped --network host \
        -e DJANGO_DB_HOST=192.168.1.201 -e DJANGO_DB_PORT=3306 \
        -v /volume1/docker/cono_app:/app \
        -v /volume1/docker/cono_backups:/app/backups \
        cono_api:latest sh -c 'while true; do $BACKUP_CMD; sleep 300; done'"
fi

echo "==> 7/7 校验 ..."
page=""; api=""; old=""
for _ in $(seq 1 10); do
  page=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://192.168.1.202:8001/ || true)
  api=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://192.168.1.202:8001/api/ || true)
  [ "$page" = "200" ] && [ "$api" = "401" ] && break
  sleep 3
done
old=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://192.168.1.202:8000/login/ || true)
echo "    新版前端 : $page   (期望 200)"
echo "    新版 API  : $api   (期望 401，代表服务已响应未认证请求)"
echo "    老版系统  : $old   (期望 200)"

# /api/ 返回 401 只能说明服务活着，表缺失时它照样 401，所以这里直接查表结构，
# 避免「脚本报成功、页面却 500」。未执行的迁移数必须为 0。
pending=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_api python manage.py showmigrations cono --plan 2>/dev/null | grep -c '\\[ \\]' || true")
echo "    待执行迁移: ${pending:-?}   (期望 0)"
[ "$page" = "200" ] || { echo "!! 新版前端异常"; exit 1; }
[ "$api" = "401" ] || { echo "!! 新版 API 异常"; exit 1; }
[ "$old" = "200" ] || { echo "!! 老版系统异常"; exit 1; }
[ "$pending" = "0" ] || { echo "!! 还有未执行的数据库迁移"; exit 1; }
echo "==> 部署完成: http://192.168.1.202:8001/"
