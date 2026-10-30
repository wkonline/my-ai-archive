#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
HOST="cono-nas"
DEST="/volume1/docker/cono_app"
DOCKER="/var/packages/ContainerManager/target/usr/bin/docker"

SSH_OPTS=(-o BatchMode=yes)

echo "==> 正在上传代码到 NAS:$DEST ..."
# 代码目录以 bind mount 挂载进容器，无需重建镜像，上传后重启即可生效
tar --exclude='./.venv' \
    --exclude='./__pycache__' \
    --exclude='./.idea' \
    --exclude='./.git' \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='./backup' \
    --exclude='./backups' \
    --exclude='./media' \
    --exclude='./staticfiles' \
    -C "$ROOT" -czf - . 2>/dev/null | ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p $DEST && tar -xzf - -C $DEST"

echo "==> 正在检查容器内依赖 ..."
MISSING=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python -c \"
import importlib.util as u
need = ['xlrd', 'pandas', 'openpyxl', 'django']
print(','.join(m for m in need if u.find_spec(m) is None))
\"")

if [ -n "$MISSING" ]; then
    echo "==> 容器缺少依赖: $MISSING，正在安装 ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web pip install --no-cache-dir $MISSING"
else
    echo "==> 依赖齐全"
fi

echo "==> 正在执行数据库迁移 ..."
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python manage.py migrate --noinput 2>&1 | tail -3"

echo "==> 正在收集静态文件并重启网站容器 ..."
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python manage.py collectstatic --noinput 2>&1 | tail -2 && sudo -n $DOCKER restart cono_web"

echo "==> 正在检查定时备份容器 ..."
# 每天 11:00 自动备份数据库：由独立的 cono_backup 容器每 5 分钟检查一次，
# 到点且当天还没备份时执行 python manage.py backup_database --if-due
if ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER ps -a --format '{{.Names}}' | grep -qx cono_backup"; then
    echo "==> cono_backup 已存在"
else
    echo "==> 创建定时备份容器 cono_backup ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER run -d --name cono_backup \
        --restart unless-stopped --network host \
        -e DJANGO_SECRET_KEY=nas-cono-deploy-key-2026 -e DJANGO_DEBUG=false \
        -v /volume1/docker/cono_app:/app \
        -v /volume1/docker/cono_backups:/app/backups \
        cono_web sh -c 'while true; do python manage.py backup_database --if-due; sleep 300; done'"
fi

echo "==> 正在校验 ..."
sleep 6
ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python -c 'import xlrd; print(\"    xlrd\", xlrd.__version__)'"
curl -s -o /dev/null -w "    站点状态: %{http_code}\n" --max-time 15 http://192.168.1.202:8000/login/

echo "==> 同步完成，刷新 http://192.168.1.202:8000 即可。"
