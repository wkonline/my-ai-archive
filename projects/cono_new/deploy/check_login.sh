#!/bin/bash
# 对比老系统与新 API 实际使用的密码盐，定位“用户名或密码错误”。
#
#   ./deploy/check_login.sh [用户名]
#
# 老密码哈希 = md5(盐 + 明文)。老系统取 SECRET_KEY，新 API 取 LEGACY_SECRET_KEY。
# 两者必须相同且等于生产容器 cono_web 的 DJANGO_SECRET_KEY（nas-cono-deploy-key-2026），
# 否则库里存的哈希与算出来的对不上，登录一律失败。
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/api/.venv/bin/python"
USERNAME="${1:-}"

if [ ! -x "$PY" ]; then
    echo "找不到 $PY，请先运行 ./deploy/dev.sh 初始化环境"
    exit 1
fi

fp() { "$PY" -c "import hashlib,sys;print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:8])" "$1"; }

PROD='nas-cono-deploy-key-2026'
echo "== 生产容器 cono_web 使用的盐指纹（库里哈希就是用它算的）=="
echo "   $(fp "$PROD")   <- $PROD"
echo

echo "== 老系统（8000）实际会用到的盐 =="
cd "$ROOT"
DJANGO_SETTINGS_MODULE=local_test_settings "$PY" - <<'PY'
import os, hashlib, django
django.setup()
from django.conf import settings
s = settings.SECRET_KEY
print(f"   {hashlib.md5(s.encode()).hexdigest()[:8]}   <- SECRET_KEY = {s[:24]}...")
src = 'DJANGO_SECRET_KEY 环境变量' if os.environ.get('DJANGO_SECRET_KEY') else 'settings.py 里的默认值'
print(f"   来源: {src}")
PY
echo

echo "== 新 API（8001）校验老密码时用的盐 =="
cd "$ROOT/api"
DJANGO_SETTINGS_MODULE=cono_api.settings "$PY" - <<'PY'
import os, hashlib, django
django.setup()
from django.conf import settings
s = settings.LEGACY_SECRET_KEY
print(f"   {hashlib.md5(s.encode()).hexdigest()[:8]}   <- LEGACY_SECRET_KEY = {s[:24]}...")
src = 'LEGACY_SECRET_KEY 环境变量' if os.environ.get('LEGACY_SECRET_KEY') else 'settings.py 里的默认值'
print(f"   来源: {src}")
PY
echo

echo "== 结论 =="
echo "   上面两个指纹都应是 $(fp "$PROD")。若老系统那个不是，"
echo "   说明 8000 进程用的盐不对：停掉它，用 ./deploy/dev.sh 重新启动。"
if [ -n "$USERNAME" ]; then
    echo
    echo "== 账号 $USERNAME 的详细诊断 =="
    cd "$ROOT"
    "$PY" manage.py diagnose_login "$USERNAME" --settings=local_test_settings
fi
