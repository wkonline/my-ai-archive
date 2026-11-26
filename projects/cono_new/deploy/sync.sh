#!/bin/bash
# NAS 部署统一入口（192.168.1.202）
#
# 用法：
#   ./deploy/sync.sh old         老版系统（前后端不分离，8000）
#   ./deploy/sync.sh new         新版系统（前后端分离，8001 → API 8002）
#   ./deploy/sync.sh vue [文件]  只同步前端产物（可选指定单个组件）
#   ./deploy/sync.sh all         先 old 再 new
#
# 环境变量：
#   DRY_RUN=1   只打印将要从 NAS 删除的文件，不实际删除
#   PRUNE=0     不同步删除，保留 NAS 上多余的文件
#
# 线上架构：
#   8000  cono_web      老版 Django（容器，代码 bind mount）
#   8001  cono_web_new  Nginx：静态前端 + /api/ 反代到 127.0.0.1:8002
#   8002  cono_api      新版 DRF 后端（Gunicorn，工作目录 /app/api）
# 数据库不在 NAS 上：两个系统共用 192.168.1.201:3306 的 cono 库与 media 卷。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="cono-nas"
DEST="/volume1/docker/cono_app"
DOCKER="/var/packages/ContainerManager/target/usr/bin/docker"
SSH_OPTS=(-o BatchMode=yes -o ControlMaster=no -o ControlPath=none -o StrictHostKeyChecking=accept-new)

# NAS 上的 media、backups 是独立挂载目录，覆盖会丢数据；
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
  --exclude='local_cono.sqlite3'
  --exclude='media'
  --exclude='staticfiles'
  --exclude='backups'
  --exclude='frontend/dist'
  --exclude='.venv'
)

# NAS 上的 /usr/bin/rsync 是群晖 setuid 特制版，不支持 --server 模式
# （报 "rsync service is no running"），所以统一用 tar over ssh。
#
# tar 解包只覆盖同名文件、从不删除，因此本地删掉的文件会一直留在 NAS 上。
# 同步后再对比两端文件清单，删掉远端独有的文件（prune_remote）。
# 只存在于远端的用户数据与运行时产物不参与比对，见 PRUNE_FIND 的排除项。
PRUNE_FIND=(
  -type f
  -not -path './.git/*'
  -not -path './api/.venv/*'
  -not -path './frontend/node_modules/*'
  -not -path '*/__pycache__/*'
  -not -path './media/*'
  -not -path './backups/*'
  -not -path './staticfiles/*'
  -not -path './frontend/dist/*'
  -not -path './.idea/*'
  -not -path './.vscode/*'
  -not -path './.chrome-profile/*'
  -not -path './.vite/*'
  -not -name '*.pyc'
  -not -name '.DS_Store'
  -not -name '._*'
  -not -name 'db.sqlite3'
  -not -name 'local_cono.sqlite3'
)

upload_repo() {
  echo "==> 整仓同步到 $HOST:$DEST ..."
  COPYFILE_DISABLE=1 tar -czf - "${EXCLUDES[@]}" -C "$ROOT" . \
    | ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p $DEST && tar -xzf - -C $DEST"
  if [ "${PRUNE:-1}" = "0" ]; then
    echo "    (PRUNE=0，保留远端多余文件)"
    return 0
  fi
  prune_remote
}

# 删除远端独有的文件，让 NAS 与本地保持一致。
# 任何一步异常都直接放弃删除——留下多余文件远比误删线上数据安全。
prune_remote() {
  local tmp_local tmp_remote tmp_del remote_find e
  tmp_local=$(mktemp); tmp_remote=$(mktemp); tmp_del=$(mktemp)

  if ! ( cd "$ROOT" && find . "${PRUNE_FIND[@]}" ) | LC_ALL=C sort > "$tmp_local"; then
    rm -f "$tmp_local" "$tmp_remote" "$tmp_del"
    echo "!! 无法生成本地文件清单，跳过删除步骤"
    return 0
  fi
  if [ ! -s "$tmp_local" ]; then
    rm -f "$tmp_local" "$tmp_remote" "$tmp_del"
    echo "!! 本地文件清单为空，跳过删除步骤"
    return 0
  fi

  # 远端执行同一个 find 表达式，逐项加单引号以免 * 被远端 shell 展开
  remote_find=""
  for e in "${PRUNE_FIND[@]}"; do remote_find+=" '$e'"; done

  if ! ssh "${SSH_OPTS[@]}" "$HOST" "cd '$DEST' && find . $remote_find" 2>/dev/null \
      | LC_ALL=C sort > "$tmp_remote"; then
    rm -f "$tmp_local" "$tmp_remote" "$tmp_del"
    echo "!! 无法获取远端文件清单，跳过删除步骤"
    return 0
  fi
  # 清单为空说明 cd/find 出了问题，此时做差集会把远端文件全部当成多余
  if [ ! -s "$tmp_remote" ]; then
    rm -f "$tmp_local" "$tmp_remote" "$tmp_del"
    echo "!! 远端文件清单为空（$DEST 可能不存在），跳过删除步骤"
    return 0
  fi

  LC_ALL=C comm -13 "$tmp_local" "$tmp_remote" > "$tmp_del"
  rm -f "$tmp_local" "$tmp_remote"

  if [ ! -s "$tmp_del" ]; then
    rm -f "$tmp_del"
    echo "    远端无多余文件"
    return 0
  fi

  echo "==> 清理远端多余文件 $(wc -l < "$tmp_del" | tr -d ' ') 个 ..."
  sed 's|^\./||' "$tmp_del" | head -10 | sed 's/^/      /'
  if [ "$(wc -l < "$tmp_del")" -gt 10 ]; then
    echo "      ..."
  fi

  if [ "${DRY_RUN:-}" = "1" ]; then
    rm -f "$tmp_del"
    echo "    (DRY_RUN=1，未实际删除)"
    return 0
  fi

  # 清单走 stdin 逐行 rm；文件名不拼进命令，避免引号与空格问题
  if ! ssh "${SSH_OPTS[@]}" "$HOST" "cd '$DEST' && while IFS= read -r f; do rm -f -- \"\$f\"; done" \
      < "$tmp_del"; then
    rm -f "$tmp_del"
    echo "!! 删除远端文件失败"
    return 0
  fi
  rm -f "$tmp_del"

  # 删空的目录一并清掉；受保护目录即使为空也不动
  ssh "${SSH_OPTS[@]}" "$HOST" "cd '$DEST' && find . -mindepth 1 -type d -empty \
      -not -path './media*' -not -path './backups*' -not -path './staticfiles*' \
      -not -path './frontend/dist*' -not -path './api/.venv*' \
      -not -path './frontend/node_modules*' -not -path './.git*' \
      -delete 2>/dev/null || true"
}


sync_old() {
  echo "==> [old] 上传老版代码 ..."
  # 老版代码以 bind mount 挂载进容器，无需重建镜像，上传后重启即可生效
  upload_repo

  echo "==> [old] 检查容器内依赖 ..."
  local missing
  missing=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python -c \"
import importlib.util as u
need = ['xlrd', 'pandas', 'openpyxl', 'django']
print(','.join(m for m in need if u.find_spec(m) is None))
\"")
  if [ -n "$missing" ]; then
    echo "==> [old] 容器缺少依赖: ${missing}，正在安装 ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web pip install --no-cache-dir $missing"
  else
    echo "==> [old] 依赖齐全"
  fi

  echo "==> [old] 执行数据库迁移 ..."
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python manage.py migrate --noinput 2>&1 | tail -3"

  echo "==> [old] 收集静态文件并重启容器 ..."
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python manage.py collectstatic --noinput 2>&1 | tail -2 && sudo -n $DOCKER restart cono_web"

  ensure_old_backup_container

  echo "==> [old] 校验 ..."
  sleep 6
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web python -c 'import xlrd; print(\"    xlrd\", xlrd.__version__)'"
  curl -s -o /dev/null -w "    老版站点: %{http_code}  (期望 200)\n" --max-time 15 http://192.168.1.202:8000/login/
  echo "==> [old] 完成，刷新 http://192.168.1.202:8000 即可。"
}

# 老版备份容器：每天 11:00 由 cono_backup 每 5 分钟检查一次，到点且当天未备份才执行
ensure_old_backup_container() {
  if ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER ps -a --format '{{.Names}}' | grep -qx cono_backup"; then
    echo "==> [old] cono_backup 已存在"
    return
  fi
  echo "==> [old] 创建定时备份容器 cono_backup ..."
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER run -d --name cono_backup \
      --restart unless-stopped --network host \
      -e DJANGO_SECRET_KEY=nas-cono-deploy-key-2026 -e DJANGO_DEBUG=false \
      -v /volume1/docker/cono_app:/app \
      -v /volume1/docker/cono_backups:/app/backups \
      cono_web sh -c 'while true; do python manage.py backup_database --if-due; sleep 300; done'"
}

sync_new() {
  echo "==> [new] 1/7 重新构建前端 ..."
  ( cd "$ROOT/frontend" && npm run build )

  echo "==> [new] 2/7 整仓同步 ..."
  # 新版后端依赖仓库根目录的 cono/（复用老版模型）和 cono_new/settings.py
  # （CONO_PERMISSION / CONO_MENU），所以必须整仓同步，不能只传 api/。
  upload_repo

  echo "==> [new] 3/7 同步前端产物（原地覆盖 + 清理旧 hash 文件）..."
  # 必须原地覆盖：nginx 容器的 /usr/share/nginx/html 是 bind mount，
  # 一旦把 dist 目录整体换掉（mv 成新 inode），容器里的挂载仍指向已删除的旧目录，会 403。
  COPYFILE_DISABLE=1 tar -czf - -C "$ROOT/frontend/dist" . \
    | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C $DEST/frontend/dist"

  local tmp_remote tmp_local tmp_del
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

  echo "==> [new] 4/7 重建 API 镜像（同步 pip 依赖）..."
  # Python 依赖烤在镜像里，requirements.txt 变化必须重建镜像
  ssh "${SSH_OPTS[@]}" "$HOST" "cd $DEST/api && sudo -n $DOCKER build -q -t cono_api:latest . >/tmp/cono_api_build.log 2>&1 && echo '    镜像已更新' || { echo '!! 镜像构建失败，容器保持原状'; tail -20 /tmp/cono_api_build.log; exit 1; }"

  echo "==> [new] 5/7 重建 API 容器 ..."
  # restart 不会切换到新镜像，必须 rm + run；-w /app/api 让 cono_api 包可导入
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER rm -f cono_api >/dev/null 2>&1 || true; \
    sudo -n $DOCKER run -d --name cono_api --restart unless-stopped --network host \
      -w /app/api \
      -e DJANGO_SECRET_KEY=nas-cono-new-api-key-2026 \
      -e LEGACY_SECRET_KEY=nas-cono-deploy-key-2026 \
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

  echo "==> [new] 6/7 执行数据库迁移 ..."
  # 容器重建后新代码已生效，但表结构还没跟上，少了这步新增迁移对应的页面会 500。
  # 走 cono_api（工作目录 /app/api，PyMySQL），与备份命令同一条路径。
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_api python manage.py migrate --noinput 2>&1 | tail -5"

  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_web_new nginx -t >/dev/null 2>&1 && sudo -n $DOCKER exec cono_web_new nginx -s reload >/dev/null 2>&1 && echo '    Nginx 已重载'"

  ensure_new_backup_container

  echo "==> [new] 7/7 校验 ..."
  local page="" api="" old=""
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

  # /api/ 返回 401 只能说明服务活着，表缺失时照样 401，所以直接查未执行迁移数
  local pending
  pending=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER exec cono_api python manage.py showmigrations cono --plan 2>/dev/null | grep -c '\\[ \\]' || true")
  echo "    待执行迁移: ${pending:-?}   (期望 0)"
  [ "$page" = "200" ] || { echo "!! 新版前端异常"; exit 1; }
  [ "$api" = "401" ] || { echo "!! 新版 API 异常"; exit 1; }
  [ "$old" = "200" ] || { echo "!! 老版系统异常"; exit 1; }
  [ "$pending" = "0" ] || { echo "!! 还有未执行的数据库迁移"; exit 1; }
  echo "==> [new] 完成: http://192.168.1.202:8001/"
}

# 新版备份容器：每天 23:00，保留 60 天
# 必须走 api/manage.py（cono_api.settings 用 PyMySQL 充当 MySQLdb）；cono_api 镜像里
# 没有 mysqlclient，跑根目录 manage.py（cono_new.settings）会直接 ImproperlyConfigured。
ensure_new_backup_container() {
  local backup_cmd
  backup_cmd=$(ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER inspect -f '{{join .Config.Cmd \" \"}}' cono_backup 2>/dev/null" || true)
  # 早期部署创建的 cono_backup 用的是旧命令，会静默失败，检测到不一致就重建
  if [ -n "$backup_cmd" ] && [[ "$backup_cmd" != *"api/manage.py"* ]]; then
    echo "==> [new] cono_backup 命令已过期，重建 ..."
    ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER rm -f cono_backup >/dev/null 2>&1 || true"
    backup_cmd=""
  fi
  if [ -n "$backup_cmd" ]; then
    echo "==> [new] cono_backup 已存在"
    return
  fi
  echo "==> [new] 创建定时备份容器 cono_backup ..."
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo -n $DOCKER run -d --name cono_backup \
      --restart unless-stopped --network host \
      -e DJANGO_DB_HOST=192.168.1.201 -e DJANGO_DB_PORT=3306 \
      -v /volume1/docker/cono_app:/app \
      -v /volume1/docker/cono_backups:/app/backups \
      cono_api:latest sh -c 'while true; do python api/manage.py backup_database --if-due --retention-days 60; sleep 300; done'"
}

sync_vue() {
  local src_path="${1:-}"
  local assets="/volume1/docker/cono_app/frontend/dist/assets"
  local tmp_local tmp_remote
  tmp_local=$(mktemp); tmp_remote=$(mktemp)

  if [ -z "$src_path" ]; then
    src_path=$(git -C "$ROOT" diff --name-only HEAD -- frontend/src/ || true)
    [ -z "$src_path" ] && { echo "==> 无 git 变更，请指定要同步的文件"; exit 1; }
  fi

  echo "==> [vue] 重新构建前端 ..."
  ( cd "$ROOT/frontend" && npm run build >/dev/null 2>&1 )

  local name h
  for f in "$ROOT/frontend/dist/assets/"*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    case "$name" in index.html|favicon.svg|icons.svg|logo.png) continue ;; esac
    h=$(md5sum "$f" | awk '{print $1}')
    echo "${h}  ${name}"
  done | sort > "$tmp_local"

  ssh "${SSH_OPTS[@]}" "$HOST" "
    cd '$assets'
    for f in *; do
      [ -f \"\$f\" ] || continue
      case \"\$f\" in
        index.html|favicon.svg|icons.svg|logo.png) continue ;;
      esac
      h=\$(md5sum \"\$f\" 2>/dev/null | awk '{print \$1}')
      echo \"\$h  \$f\"
    done
  " | sort > "$tmp_remote" 2>/dev/null || true

  # 找出需要上传的文件（hash 不同，或本地有远程没有的新文件）
  local upload_list=() remote_match
  while read -r line; do
    h="${line%%  *}"
    name="${line#*  }"
    remote_match=$(grep "  ${name}$" "$tmp_remote" 2>/dev/null | head -1 || true)
    if [ -z "$remote_match" ] || [ "${remote_match%%  *}" != "$h" ]; then
      upload_list+=("$name")
    fi
  done < "$tmp_local"

  if [ ${#upload_list[@]} -eq 0 ]; then
    echo "==> [vue] 所有资产已是最新，无需同步"
    exit 0
  fi

  echo "==> [vue] 需要同步 ${#upload_list[@]} 个变更文件："
  printf '      %s\n' "${upload_list[@]}"
  COPYFILE_DISABLE=1 tar -czf - -C "$ROOT/frontend/dist/assets" "${upload_list[@]}" \
    | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C $assets"
  rm -f "$tmp_local" "$tmp_remote"
  echo "==> [vue] 完成。硬刷新浏览器（Cmd/Ctrl+Shift+R）即可看到效果。"
}

case "${1:-}" in
  old)  sync_old ;;
  new)  sync_new ;;
  vue)  shift; sync_vue "${1:-}" ;;
  all)  sync_old; sync_new ;;
  *)
    sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
