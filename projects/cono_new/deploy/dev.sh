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
    command -v "$PY3" >/dev/null 2>&1 || { echo "找不到 $PY3，请先安装 Python 3.11 及以上版本"; exit 1; }
    echo "==> 初始化虚拟环境 $VENV（首次运行，需要联网下载依赖）"
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

# 老系统与新系统读同一套环境变量决定用 MySQL 还是 SQLite
if [ "${USE_SQLITE:-}" = "1" ]; then
    export CONO_LOCAL_DB_PATH="${CONO_LOCAL_DB_PATH:-$ROOT/local_cono.sqlite3}"
    echo "使用本地 SQLite: $CONO_LOCAL_DB_PATH"
fi

if port_alive 8000; then
    echo "老版系统已在运行 (8000)，跳过"
else
    echo "启动老版系统 (runserver)..."
    cd "$ROOT"
    # api/.venv 没有 whitenoise/mysqlclient，用 local_test_settings 把它们去掉
    nohup "$PY" manage.py runserver 0.0.0.0:8000 --noreload \
        --settings=local_test_settings > /tmp/cono-old.log 2>&1 &
    echo "老版 PID: $!"
fi

if port_alive 8001; then
    echo "新版 API 已在运行 (8001)，跳过"
else
    echo "启动新版 API (gunicorn)..."
    cd "$ROOT/api"
    nohup "$PY" -m gunicorn cono_api.wsgi:application \
        --bind 127.0.0.1:8001 --workers 2 --timeout 120 \
        > /tmp/gunicorn.log 2>&1 &
    echo "API PID: $!"
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
echo "登录: admin / 123456"
