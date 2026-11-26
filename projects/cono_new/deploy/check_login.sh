#!/bin/bash
# 对比老系统与新 API 实际使用的密码盐，定位“用户名或密码错误”。
#
#   ./deploy/check_login.sh [用户名]
#
# 老密码哈希 = md5(盐 + 明文)。老系统取 SECRET_KEY，新 API 取 LEGACY_SECRET_KEY。
# 两者必须相同且等于生产容器 cono_web 的 DJANGO_SECRET_KEY（nas-cono-deploy-key-2026），
# 否则库里存的哈希与算出来的对不上，登录一律失败。
#
# 优先读取【正在运行的进程】的环境变量（ps eww），因为那才是真正生效的盐；
# 进程没在跑时退回按 settings.py 推算，并明确标注这一点。
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/api/.venv/bin/python"
USERNAME="${1:-}"
PROD='nas-cono-deploy-key-2026'

if [ ! -x "$PY" ]; then
    echo "找不到 $PY，请先运行 ./deploy/dev.sh 初始化环境"
    exit 1
fi

fp() { "$PY" -c "import hashlib,sys;print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:8])" "$1"; }

PROD_FP="$(fp "$PROD")"
echo "== 生产容器 cono_web 使用的盐（库里哈希就是用它算的）=="
echo "   $PROD_FP   <- $PROD"
echo

# 取指定端口上监听进程的某个环境变量
# $1=端口 $2=变量名 $3=进程特征串（没有 lsof 时用来定位进程）
port_env() {
    local port="$1" var="$2" pattern="${3:-}" pid=""
    if command -v lsof >/dev/null 2>&1; then
        pid="$(lsof -nP -ti:"$port" 2>/dev/null | head -1)"
    elif [ -n "$pattern" ]; then
        pid="$(ps aux | grep -F "$pattern" | grep -v grep | awk '{print $2}' | head -1)"
    fi
    [ -n "$pid" ] || return 1
    ps eww -p "$pid" -o command= 2>/dev/null \
        | tr ' ' '\n' | sed -n "s/^${var}=//p" | head -1
}

# 打印某端口进程的盐：优先真实环境变量，其次按 settings.py 推算
# $1=端口 $2=settings 里的变量名 $3=settings 模块 $4=工作目录 $5=环境变量名 $6=进程特征串
report_port_salt() {
    local port="$1" var="$2" settings_mod="$3" workdir="$4" envvar="$5" pattern="${6:-}"
    local val
    if val="$(port_env "$port" "$envvar" "$pattern")"; then
        if [ -n "$val" ]; then
            echo "   $(fp "$val")   <- $envvar = ${val:0:24}..."
            echo "   来源: 端口 $port 运行中进程的环境变量（真实生效值）"
        else
            echo "   （端口 $port 进程未设置 $envvar，实际退回 settings.py 默认值）"
            echo "   来源: 端口 $port 进程没有该环境变量"
        fi
        return
    fi
    echo "   （端口 $port 没有进程在监听，以下为按当前环境推算，非运行中进程的真实值）"
    ( cd "$workdir" && DJANGO_SETTINGS_MODULE="$settings_mod" ENVVAR="$envvar" "$PY" - <<PY
import os, hashlib, django
django.setup()
from django.conf import settings
s = getattr(settings, '$var')
print(f"   {hashlib.md5(s.encode()).hexdigest()[:8]}   <- $var = {s[:24]}...")
envvar = os.environ['ENVVAR']
src = f'环境变量 {envvar}（当前 shell 已导出）' if os.environ.get(envvar) else 'settings.py 默认值'
print(f"   来源: {src}")
PY
    )
}

echo "== 老系统（8000）=="
report_port_salt 8000 SECRET_KEY local_test_settings "$ROOT" DJANGO_SECRET_KEY "runserver 0.0.0.0:8000"
echo

echo "== 新 API（8001）=="
report_port_salt 8001 LEGACY_SECRET_KEY cono_api.settings "$ROOT/api" LEGACY_SECRET_KEY "gunicorn cono_api.wsgi"
echo

echo "== 结论 =="
echo "   库里的哈希由 $PROD_FP 生成。老系统若与之不符，登录必定失败。"
echo "   修复：lsof -ti:8000 | xargs kill && unset DJANGO_SECRET_KEY && ./deploy/dev.sh"
if [ -n "$USERNAME" ]; then
    echo
    echo "== 账号 $USERNAME 的详细诊断 =="
    cd "$ROOT"
    "$PY" manage.py diagnose_login "$USERNAME" --settings=local_test_settings
fi
