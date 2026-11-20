"""数据库备份/还原 API（新版程序）—— 独立注册，不依赖 router.

恢复操作改为异步后台执行，HTTP 立即返回任务状态，
通过 /api/backup/restore/status/ 查询进度。

这些视图不经过 DRF 的权限体系，因此每个入口都要显式校验登录与权限码，
否则任何人都能下载/覆盖整个数据库。
"""
import datetime
import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path

from django.core.cache import cache

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings

from api.core.permissions import get_effective_permissions

# 备份文件名只允许这些字符，杜绝 ../ 与绝对路径穿越
_SAFE_NAME_RE = re.compile(r'^[A-Za-z0-9_.-]+\.sql$')


def _auth_error(request, permission_code):
    """校验登录状态与权限码，通过返回 None，否则返回 JsonResponse。"""
    from api.core.authentication import CoreUserJWTAuthentication
    from rest_framework.exceptions import AuthenticationFailed

    try:
        auth = CoreUserJWTAuthentication().authenticate(request)
    except AuthenticationFailed:
        auth = None
    if not auth:
        return JsonResponse({'detail': '身份认证信息未提供。'}, status=401)
    request.user, _ = auth
    if getattr(request.user, 'role', '') == 'admin':
        return None
    perms = get_effective_permissions(request.user)
    if perms is None or permission_code in perms:
        return None
    return JsonResponse({'detail': '无权访问'}, status=403)


def _backup_file(name):
    """把文件名解析为备份目录内的文件；非法名或越界返回 None。"""
    name = (name or '').strip()
    if not _SAFE_NAME_RE.match(name):
        return None
    return _backup_dir() / name


def _redact(text):
    """把 stderr 里的数据库密码替换成 ******，避免随接口返回或落日志。"""
    password = _db_config()['password']
    if password and text:
        return text.replace(password, '******')
    return text


def _db_config():
    return {
        'user': os.environ.get('DJANGO_DB_USER', 'cono'),
        'password': os.environ.get('DJANGO_DB_PASSWORD', 'cono2024'),
        'name': os.environ.get('DJANGO_DB_NAME', 'cono'),
        'host': os.environ.get('DJANGO_DB_HOST', '192.168.1.201'),
        'port': os.environ.get('DJANGO_DB_PORT', '3306'),
    }


def _no_ssl_args(client):
    """MariaDB 客户端默认校验服务端证书，连自签证书的 MySQL 会报 TLS 错误，需关闭 SSL。
    两种客户端参数不同：MariaDB 只认 --skip-ssl，Oracle MySQL 只认 --ssl-mode=DISABLED。"""
    try:
        r = subprocess.run([client, '--version'], capture_output=True, timeout=10)
        version = (r.stdout or b'').decode('utf-8', 'replace').lower()
    except (OSError, subprocess.SubprocessError):
        version = ''
    if 'mariadb' in version:
        return ['--skip-ssl']
    return ['--ssl-mode=DISABLED']


def _mysql_bin():
    return os.environ.get('DJANGO_MYSQL_BIN', '/usr/bin/mysql')


def _mysqldump_bin():
    return os.environ.get('DJANGO_MYSQLDUMP_BIN', '/usr/bin/mysqldump')


# 还原任务状态存缓存而非进程内 dict：gunicorn 多 worker 下轮询请求可能打到
# 另一个进程，进程内 dict 会永远查不到任务。缓存是文件后端，跨 worker 共享。
RESTORE_JOB_TTL = 3600


def _set_job(job_id, payload):
    cache.set('restore_job:%s' % job_id, payload, RESTORE_JOB_TTL)


def _get_job(job_id):
    return cache.get('restore_job:%s' % job_id)


def _run_restore_job(job_id, name):
    """后台执行数据库还原，结果写入缓存，供 /backup/restore/status/ 查询。"""
    _set_job(job_id, {'status': 'running', 'detail': ''})
    backup_file = _backup_dir() / name
    c = _db_config()
    cmd = [
        _mysql_bin(),
        *_no_ssl_args(_mysql_bin()),
        '-u', c['user'],
        '-h', c['host'], '-P', str(c['port']), c['name'],
    ]
    try:
        with open(backup_file, 'rb') as fh:
            r = subprocess.run(cmd, stdin=fh, capture_output=True, timeout=900,
                               env={**os.environ, 'MYSQL_PWD': c['password']})
        if r.returncode != 0:
            err = _redact((r.stderr or b'').decode(errors='replace').strip())
            _set_job(job_id, {'status': 'error', 'detail': err or 'mysql 导入失败'})
            return
        _set_job(job_id, {'status': 'success', 'detail': f'已从 {name} 恢复数据库成功'})
    except Exception as e:
        _set_job(job_id, {'status': 'error', 'detail': _redact(str(e))})


def _backup_dir():
    d = Path(getattr(settings, 'BACKUP_DIR', None) or os.environ.get('DJANGO_BACKUP_DIR', '/app/backups'))
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(d), 0o755)
    except OSError:
        pass
    return d


@csrf_exempt
def backup_list(request):
    denied = _auth_error(request, 'backup_database')
    if denied:
        return denied
    d = _backup_dir()
    files = sorted(d.glob('*.sql'), key=os.path.getmtime, reverse=True)
    items = []
    for f in files:
        st = f.stat()
        items.append({
            'name': f.name,
            'size': f'{st.st_size / 1024:.1f} KB',
            'size_bytes': st.st_size,
            'created': datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse(items, safe=False)


@csrf_exempt
def backup_create(request):
    denied = _auth_error(request, 'backup_database')
    if denied:
        return denied
    c = _db_config()
    cmd = [
        _mysqldump_bin(), '--no-tablespaces',
        *_no_ssl_args(_mysqldump_bin()),
        '-u', c['user'],
        '-h', c['host'], '-P', c['port'], c['name'],
    ]
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    out = _backup_dir() / f'cono_{stamp}.sql'
    try:
        with open(out, 'wb') as fh:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, timeout=300,
                               env={**os.environ, 'MYSQL_PWD': c['password']})
        if r.returncode != 0 or out.stat().st_size == 0:
            err = _redact((r.stderr or b'').decode(errors='replace').strip())
            if out.exists():
                out.unlink()
            return JsonResponse({'detail': err or 'mysqldump 失败'}, status=500)
        try:
            os.chown(str(out), 33, 33)
        except OSError:
            pass
        return JsonResponse({'message': '备份成功', 'name': out.name,
                             'size': f'{out.stat().st_size / 1024:.1f} KB'})
    except FileNotFoundError:
        return JsonResponse({'detail': 'mysqldump 未找到，请安装 default-mysql-client'}, status=500)
    except subprocess.TimeoutExpired:
        if out.exists():
            out.unlink()
        return JsonResponse({'detail': '备份超时（超过 5 分钟）'}, status=504)


@csrf_exempt
def backup_restore(request):
    """从指定的 .sql 文件恢复数据库（异步执行，立即返回 job_id）。"""
    denied = _auth_error(request, 'restore_database')
    if denied:
        return denied
    name = ''
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '').strip()
    except Exception:
        pass
    if not name:
        return JsonResponse({'detail': '请提供备份文件名'}, status=400)
    backup_file = _backup_file(name)
    if backup_file is None or not backup_file.exists():
        return JsonResponse({'detail': f'备份文件不存在：{name}'}, status=404)
    job_id = uuid.uuid4().hex
    t = threading.Thread(target=_run_restore_job, args=(job_id, name), daemon=True)
    t.start()
    return JsonResponse({'job_id': job_id, 'message': '恢复任务已启动'})


@csrf_exempt
def backup_restore_status(request):
    """查询恢复任务状态：running / success / error。"""
    denied = _auth_error(request, 'restore_database')
    if denied:
        return denied
    job_id = request.GET.get('job_id', '').strip()
    if not job_id:
        return JsonResponse({'detail': '请提供 job_id'}, status=400)
    job = _get_job(job_id)
    if not job:
        return JsonResponse({'status': 'running', 'detail': '任务尚未开始'})
    return JsonResponse(job)

@csrf_exempt
def backup_delete(request):
    denied = _auth_error(request, 'backup_database')
    if denied:
        return denied
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '').strip()
    except Exception:
        name = ''
    if not name:
        return JsonResponse({'detail': '请提供备份文件名'}, status=400)
    backup_file = _backup_file(name)
    if backup_file is None or not backup_file.exists():
        return JsonResponse({'detail': f'备份文件不存在：{name}'}, status=404)
    backup_file.unlink()
    return JsonResponse({'message': f'已删除 {name}'})
