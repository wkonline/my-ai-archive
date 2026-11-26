#!/bin/bash
# 对比老系统与新 API 实际使用的密码盐，定位“用户名或密码错误”。
#
#   ./deploy/check_login.sh [用户名]
#
# 老密码哈希 = md5(盐 + 明文)。老系统取 SECRET_KEY，新 API 取 LEGACY_SECRET_KEY。
# 两者必须相同且等于生产容器 cono_web 的 DJANGO_SECRET_KEY（nas-cono-deploy-key-2026），
# 否则库里存的哈希与算出来的对不上，登录一律失败。
#
# 盐的来源按可信度依次尝试：
#   1. 端口上运行中进程的环境变量（真实生效值）
#   2. dev.sh 启动时记录的指纹文件
#   3. settings.py 推算（明确标注为非真实值）
#
# 注意：macOS 自带 bash 3.2 在变量名紧跟中文标点时会误解析，因此所有变量
# 一律写成 ${var} 形式，且不使用 set -u。
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/api/.venv/bin/python"
USERNAME="${1:-}"
PROD='nas-cono-deploy-key-2026'
STATE_DIR="${TMPDIR:-/tmp}/cono-dev-state"

if [ ! -x "${PY}" ]; then
    echo "找不到 ${PY}，请先运行 ./deploy/dev.sh 初始化环境"
    exit 1
fi

fp() { "${PY}" -c "import hashlib,sys;print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:8])" "$1"; }

PROD_FP="$(fp "${PROD}")"
echo "== 生产容器 cono_web 使用的盐（库里哈希就是用它算的）=="
echo "   ${PROD_FP}   <- ${PROD}"
echo

# 定位监听指定端口的进程；没有 lsof 时用 ps 匹配命令行
port_pid() {
    local port="$1" pattern="${2:-}"
    local pid=""
    if command -v lsof >/dev/null 2>&1; then
        pid="$(lsof -nP -ti:"${port}" 2>/dev/null | head -1)"
    fi
    if [ -z "${pid}" ] && [ -n "${pattern}" ]; then
        pid="$(ps aux | grep -F "${pattern}" | grep -v grep | awk '{print $2}' | head -1)"
    fi
    [ -n "${pid}" ] && echo "${pid}"
}

# 读进程环境变量。macOS 的 ps 不认 -o command= 拼环境，故多种写法依次尝试。
proc_env() {
    local pid="$1" var="$2"
    local out=""
    out="$(ps eww -p "${pid}" 2>/dev/null)"
    [ -n "${out}" ] || out="$(ps -E -p "${pid}" 2>/dev/null)"
    [ -n "${out}" ] || out="$(ps eww -p "${pid}" -o command= 2>/dev/null)"
    [ -n "${out}" ] || return 1
    printf '%s\n' "${out}" | tr ' ' '\n' | sed -n "s/^${var}=//p" | head -1
}

# $1=端口 $2=settings 变量名 $3=settings 模块 $4=工作目录 $5=环境变量名 $6=进程特征串
report_port_salt() {
    local port="$1" var="$2" settings_mod="$3" workdir="$4" envvar="$5" pattern="${6:-}"
    local pid="" val="" statefile="${STATE_DIR}/$1.fp8"

    pid="$(port_pid "${port}" "${pattern}")"
    if [ -n "${pid}" ]; then
        val="$(proc_env "${pid}" "${envvar}")"
        if [ -n "${val}" ]; then
            echo "   $(fp "${val}")   <- ${envvar} = ${val:0:24}..."
            echo "   来源: 端口 ${port} 运行中进程的环境变量（真实生效值，PID ${pid}）"
            return
        fi
    fi

    if [ -f "${statefile}" ]; then
        echo "   $(cat "${statefile}")   <- dev.sh 启动时使用的盐"
        echo "   来源: dev.sh 记录的指纹（进程存在但读不到其环境变量）"
        return
    fi

    if [ -n "${pid}" ]; then
        echo "   （端口 ${port} 有进程 PID ${pid}，但读不到其环境变量，也无 dev.sh 记录）"
    else
        echo "   （端口 ${port} 没有进程在监听，以下为按 settings.py 推算，非真实值）"
    fi
    ( cd "${workdir}" && DJANGO_SETTINGS_MODULE="${settings_mod}" ENVVAR="${envvar}" "${PY}" - <<PY
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
report_port_salt 8000 SECRET_KEY local_test_settings "${ROOT}" DJANGO_SECRET_KEY "runserver 0.0.0.0:8000"
echo

echo "== 新 API（8001）=="
report_port_salt 8001 LEGACY_SECRET_KEY cono_api.settings "${ROOT}/api" LEGACY_SECRET_KEY "gunicorn cono_api.wsgi"
echo

echo "== 结论 =="
echo "   登录侧按候选盐列表逐个比对，库里哈希命中任一候选盐即可登录，"
echo "   因此老系统与新 API 的盐值不同也不会导致登录失败。"
echo "   只有账号密码本身不对时才会提示“用户名或密码错误”。"
if [ -n "${USERNAME}" ]; then
    echo
    echo "== 账号 ${USERNAME} 的详细诊断 =="
    cd "${ROOT}"
    "${PY}" manage.py diagnose_login "${USERNAME}" --settings=local_test_settings
fi
