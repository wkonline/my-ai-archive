#!/bin/bash
# 本地开发启动（可重复执行：已在运行的服务会自动跳过）
#
#   8000  老版系统    Django runserver（仓库根目录 manage.py）
#   8001  新版 API    gunicorn
#   5173  新版前端    Vite dev server
#
# 数据库默认连 192.168.1.201:3306 的 cono 库。该库不可达时改用本地 SQLite：
#   USE_SQLITE=1 ./deploy/dev.sh
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/api/.venv"
PY="$VENV/bin/python"

# api/.venv 在 .gitignore 里，新克隆的仓库没有它，首次运行自动创建并装依赖
if [ ! -x "$PY" ] || ! "$PY" -c "import django" >/dev/null 2>&1; then
    PY3="${PYTHON:-python3}"
    command -v "$PY3" >/dev/null 2>&1 || { echo "找不到 ${PY3}，请先安装 Python 3.11 及以上版本"; exit 1; }
    echo "==> 初始化虚拟环境 ${VENV}（首次运行，需要联网下载依赖）"
    "$PY3" -m venv "$VENV"
    "$PY" -m pip --version >/dev/null 2>&1 || "$PY" -m ensurepip --upgrade
    "$PY" -m pip install --upgrade pip
    "$PY" -m pip install -r "$ROOT/api/requirements.txt"
    echo "==> 依赖安装完成"
fi

port_alive() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -i ":$1" >/dev/null 2>&1
    else
        # macOS 自带 lsof；精简 Linux 容器里可能没有，退回 /dev/tcp 探测
        (exec 3<>"/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1
    fi
}

# 老系统与新系统读同一套环境变量决定用 MySQL 还是 SQLite。
# 密码哈希是 md5(盐 + 明文)：老系统取 SECRET_KEY，新 API 取 LEGACY_SECRET_KEY，
# 两者必须相同且等于生产容器 cono_web 的 DJANGO_SECRET_KEY，否则连生产库时
# 算出的哈希与库里存的完全对不上，登录一律提示“用户名或密码错误”。
SALT_DEFAULT='nas-cono-deploy-key-2026'
# shell 里残留的 DJANGO_SECRET_KEY 会覆盖默认值，这是登录失败最常见的坑
if [ -n "${DJANGO_SECRET_KEY:-}" ] && [ "$DJANGO_SECRET_KEY" != "$SALT_DEFAULT" ]; then
    echo "!! 环境里已有 DJANGO_SECRET_KEY，将覆盖默认盐，老系统登录可能失败"
    echo "   当前值: ${DJANGO_SECRET_KEY:0:12}...  期望: $SALT_DEFAULT"
    echo "   如非本意请先执行: unset DJANGO_SECRET_KEY"
fi
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$SALT_DEFAULT}"
export LEGACY_SECRET_KEY="${LEGACY_SECRET_KEY:-$SALT_DEFAULT}"

if [ "${USE_SQLITE:-}" = "1" ]; then
    export CONO_LOCAL_DB_PATH="${CONO_LOCAL_DB_PATH:-$ROOT/local_cono.sqlite3}"
    echo "使用本地 SQLite: $CONO_LOCAL_DB_PATH"
    echo "==> 准备本地测试库（迁移 + 默认账号）"
    "$PY" "$ROOT/manage.py" migrate --noinput --settings=local_test_settings >/dev/null
    "$PY" "$ROOT/manage.py" ensure_dev_user --settings=local_test_settings
else
    # 库不可达时老系统会启动失败。提前探一次，避免只看到“8000 未监听”还要翻日志。
    if ! "$PY" - <<'PROBE' >/dev/null 2>&1
import os, socket
host = os.environ.get('DJANGO_DB_HOST', '192.168.1.201')
port = int(os.environ.get('DJANGO_DB_PORT', '3306'))
socket.create_connection((host, port), timeout=3).close()
PROBE
    then
        echo "!! 连不上数据库 ${DJANGO_DB_HOST:-192.168.1.201}:${DJANGO_DB_PORT:-3306}"
        echo "   生产库只在内网可达；不在局域网时请改用本地测试库：USE_SQLITE=1 ./deploy/dev.sh"
        exit 1
    fi
    echo "数据库: ${DJANGO_DB_HOST:-192.168.1.201}:${DJANGO_DB_PORT:-3306}（生产库，登录账号与生产一致）"
fi

# 端口占用就跳过会让改过盐值/库路径的老进程继续跑旧配置，登录会莫名失败。
# 记录启动时的配置指纹，变化则重启对应服务。
STATE_DIR="${TMPDIR:-/tmp}/cono-dev-state"
mkdir -p "$STATE_DIR"
DB_KEY="${CONO_LOCAL_DB_PATH:-mysql:${DJANGO_DB_HOST:-192.168.1.201}/${DJANGO_DB_NAME:-cono}}"
CONFIG_FP="$(printf '%s|%s|%s' "$DJANGO_SECRET_KEY" "$LEGACY_SECRET_KEY" "$DB_KEY" | cksum | cut -d' ' -f1)"

# 记下盐指纹（md5(盐) 前 8 位），供 check_login.sh 在无法读取进程环境变量时比对
OLD_SALT_FP="$(printf '%s' "$DJANGO_SECRET_KEY" | "$PY" -c 'import hashlib,sys;print(hashlib.md5(sys.stdin.read().encode()).hexdigest()[:8])')"
API_SALT_FP="$(printf '%s' "$LEGACY_SECRET_KEY" | "$PY" -c 'import hashlib,sys;print(hashlib.md5(sys.stdin.read().encode()).hexdigest()[:8])')"
echo "$OLD_SALT_FP" > "$STATE_DIR/8000.fp8"
echo "$API_SALT_FP" > "$STATE_DIR/8001.fp8"

# 配置指纹变了就杀掉旧进程，$1=端口 $2=服务名 $3=匹配用的命令行片段
# 按端口杀而不是按命令行匹配：gunicorn 会改写进程名，命令行匹配不到。
restart_if_stale() {
    local port="$1" name="$2" pattern="$3" fpfile="$STATE_DIR/$1.fp" pid
    port_alive "$port" || return 0
    if [ -f "$fpfile" ] && [ "$(cat "$fpfile")" = "$CONFIG_FP" ]; then
        return 1
    fi
    echo "配置已变更，重启 $name (端口 $port)..."
    if command -v lsof >/dev/null 2>&1; then
        pids="$(lsof -nP -ti:"$port" 2>/dev/null)"
    else
        pids="$(ps aux | grep -F "$pattern" | grep -v grep | awk '{print $2}')"
    fi
    for pid in $pids; do kill "$pid" 2>/dev/null || true; done
    sleep 2
    if port_alive "$port"; then
        # 还活着就强杀，仍失败才报错
        for pid in $(lsof -nP -ti:"$port" 2>/dev/null); do kill -9 "$pid" 2>/dev/null || true; done
        sleep 1
        port_alive "$port" && { echo "!! $name 未能停止，请手动结束占用 $port 的进程"; exit 1; }
    fi
    return 0
}

if restart_if_stale 8000 "老版系统" "runserver 0.0.0.0:8000"; then :; else
    echo "老版系统已在运行 (8000)，跳过"
    SKIP_OLD=1
fi
if [ "${SKIP_OLD:-}" != "1" ]; then
    echo "启动老版系统 (runserver)..."
    cd "$ROOT"
    # api/.venv 没有 whitenoise/mysqlclient，用 local_test_settings 把它们去掉
    nohup "$PY" manage.py runserver 0.0.0.0:8000 --noreload \
        --settings=local_test_settings > /tmp/cono-old.log 2>&1 &
    echo "老版 PID: $!"
    echo "$CONFIG_FP" > "$STATE_DIR/8000.fp"
fi

if restart_if_stale 8001 "新版 API" "gunicorn cono_api.wsgi"; then :; else
    echo "新版 API 已在运行 (8001)，跳过"
    SKIP_API=1
fi
if [ "${SKIP_API:-}" != "1" ]; then
    echo "启动新版 API (gunicorn)..."
    cd "$ROOT/api"
    nohup "$PY" -m gunicorn cono_api.wsgi:application \
        --bind 127.0.0.1:8001 --workers 2 --timeout 120 \
        > /tmp/gunicorn.log 2>&1 &
    echo "API PID: $!"
    echo "$CONFIG_FP" > "$STATE_DIR/8001.fp"
fi

if port_alive 5173; then
    echo "新版前端已在运行 (5173)，跳过"
else
    echo "启动新版前端 (vite)..."
    cd "$ROOT/frontend"
    # node_modules 同样不入库，缺失时先装依赖
    if [ ! -f node_modules/vite/bin/vite.js ]; then
        command -v npm >/dev/null 2>&1 || { echo "找不到 npm，请先安装 Node.js 18 及以上版本"; exit 1; }
        echo "==> 安装前端依赖（首次运行，需要联网）"
        npm install
    fi
    nohup node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 \
        > /tmp/vite.log 2>&1 &
    echo "前端 PID: $!"
fi

sleep 4
echo ""
echo "=== 状态检查 ==="
for p in 8000 8001 5173; do
    if port_alive "$p"; then echo "  $p  已监听"; else echo "  $p  未监听（看 /tmp/cono-old.log、/tmp/gunicorn.log、/tmp/vite.log）"; fi
done
echo ""
echo "老版系统: http://localhost:8000/"
echo "新版前端: http://localhost:5173/"
echo "新版 API : http://localhost:8001/"
if [ "${USE_SQLITE:-}" = "1" ]; then
    echo "本地账号: admin / admin123（SQLite 测试库，新建的）"
else
    echo "账号    : 与生产库 192.168.1.201 一致"
fi
