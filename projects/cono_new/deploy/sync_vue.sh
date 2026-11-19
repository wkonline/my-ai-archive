#!/bin/bash
# 快速同步单个 Vue 组件到 NAS（无需完整部署）
#
# 用法：
#   ./deploy/sync_vue.sh src/views/contract/ContractProductList.vue
#   ./deploy/sync_vue.sh        # 不传参数时同步 git 变更的所有前端文件
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="cono-nas"
SSH_OPTS=(-o BatchMode=yes -o ControlMaster=no -o ControlPath=none)
FTP_ASSETS="/volume1/docker/cono_app/frontend/dist/assets"

TMP_LOCAL=$(mktemp)
TMP_REMOTE=$(mktemp)
trap 'rm -f "$TMP_LOCAL" "$TMP_REMOTE"' EXIT

SRC_PATH="${1:-}"
if [ -z "$SRC_PATH" ]; then
    SRC_PATH=$(git -C "$ROOT" diff --name-only HEAD -- frontend/src/ || true)
    [ -z "$SRC_PATH" ] && { echo "==> 无 git 变更，请指定要同步的文件"; exit 1; }
fi

echo "==> 重新构建前端 ..."
cd "$ROOT/frontend" && npm run build >/dev/null 2>&1

# 列出所有本地 dist/assets 文件名 → HASH（跳过根目录文件）
local_files=""
for f in "$ROOT/frontend/dist/assets/"*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    case "$name" in index.html|favicon.svg|icons.svg|logo.png) continue ;; esac
    h=$(md5sum "$f" | awk '{print $1}')
    echo "${h}  ${name}"
done | sort > "$TMP_LOCAL"

# 列出 NAS dist/assets 文件名 → HASH
ssh "${SSH_OPTS[@]}" "$HOST" "
  cd '$FTP_ASSETS'
  for f in *; do
    [ -f \"\$f\" ] || continue
    case \"\$f\" in
      index.html|favicon.svg|icons.svg|logo.png) continue ;;
    esac
    h=\$(md5sum \"\$f\" 2>/dev/null | awk '{print \$1}')
    echo \"\$h  \$f\"
  done
" | sort > "$TMP_REMOTE" 2>/dev/null || true

# 找出需要上传的文件（hash 不同，或本地有远程没有的新文件）
upload_list=()
while read -r line; do
    h="${line%%  *}"
    name="${line#*  }"
    # 在远程列表里查同文件名是否有相同 hash
    remote_match=$(grep "  ${name}$" "$TMP_REMOTE" 2>/dev/null | head -1 || true)
    if [ -z "$remote_match" ] || [ "${remote_match%%  *}" != "$h" ]; then
        upload_list+=("$name")
    fi
done < "$TMP_LOCAL"

if [ ${#upload_list[@]} -eq 0 ]; then
    echo "==> 所有资产已是最新，无需同步"
    exit 0
fi

echo "==> 需要同步 ${#upload_list[@]} 个变更文件："
printf '      %s\n' "${upload_list[@]}"

COPYFILE_DISABLE=1 tar -czf - \
    -C "$ROOT/frontend/dist/assets" "${upload_list[@]}" \
  | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C $FTP_ASSETS"

echo "==> 完成。硬刷新浏览器（Cmd/Ctrl+Shift+R）即可看到效果。"
