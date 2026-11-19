"""数据库备份/还原 API（新版程序）—— 独立注册，不依赖 router.

恢复操作改为异步后台执行，HTTP 立即返回任务状态，
通过 /api/backup/restore/status/ 查询进度。
"""
import datetime
import json
import os
import subprocess
import threading
import time
import uuid
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings


def _db_config():
    return {
        'user': os.environ.get('DJANGO_DB_USER', 'cono'),
        'password': os.environ.get('DJANGO_DB_PASSWORD', 'cono2024'),
        'name': os.environ.get('DJANGO_DB_NAME', 'cono'),
        'host': os.environ.get('DJANGO_DB_HOST', '192.168.1.201'),
        'port': os.environ.get('DJANGO_DB_PORT', '3306'),
    }


def _no_ssl_args(client):
    """若客户端支持 --skip-ssl 则返回，否则返回空（避免版本不兼容报错）。"""
    try:
        r = subprocess.run([client, '--skip-ssl', '--version'], capture_output=True, timeout=5)
        if r.returncode == 0:
            return ['--skip-ssl']
    except Exception:
        pass
    return []


def _mysql_bin():
    return os.environ.get('DJANGO_MYSQL_BIN', '/usr/bin/mysql')


def _mysqldump_bin():
    return os.environ.get('DJANGO_MYSQLDUMP_BIN', '/usr/bin/mysqldump')


_restore_jobs = {}
_restore_jobs_lock = threading.Lock()


def _run_restore_job(job_id, name):
    """后台执行数据库还原，结果写入 _restore_jobs，供 /backup/restore/status/ 查询。"""
    with _restore_jobs_lock:
        _restore_jobs[job_id] = {'status': 'running', 'detail': ''}
    backup_file = _backup_dir() / name
    c = _db_config()
    cmd = [
        _mysql_bin(),
        *_no_ssl_args(_mysql_bin()),
        '-u', c['user'], f"-p{c['password']}",
        '-h', c['host'], '-P', str(c['port']), c['name'],
    ]
    try:
        with open(backup_file, 'rb') as fh:
            r = subprocess.run(cmd, stdin=fh, capture_output=True, timeout=900)
        if r.returncode != 0:
            err = (r.stderr or b'').decode(errors='replace').strip()
            with _restore_jobs_lock:
                _restore_jobs[job_id] = {'status': 'error', 'detail': err or 'mysql 导入失败'}
            return
        with _restore_jobs_lock:
            _restore_jobs[job_id] = {'status': 'success', 'detail': f'已从 {name} 恢复数据库成功'}
    except Exception as e:
        with _restore_jobs_lock:
            _restore_jobs[job_id] = {'status': 'error', 'detail': str(e)}


def _backup_dir():
    d = Path(os.environ.get('DJANGO_BACKUP_DIR', '/app/backups'))
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(d), 0o755)
    except OSError:
        pass
    return d


@csrf_exempt
def backup_list(request):
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
    c = _db_config()
    cmd = [
        _mysqldump_bin(), '--no-tablespaces',
        *_no_ssl_args('mysqldump'),
        '-u', c['user'], f"-p{c['password']}",
        '-h', c['host'], '-P', c['port'], c['name'],
    ]
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    out = _backup_dir() / f'cono_{stamp}.sql'
    try:
        with open(out, 'wb') as fh:
            r = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, timeout=300)
        if r.returncode != 0 or out.stat().st_size == 0:
            err = (r.stderr or b'').decode(errors='replace').strip()
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
    name = ''
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '').strip()
    except Exception:
        pass
    if not name:
        return JsonResponse({'detail': '请提供备份文件名'}, status=400)
    backup_file = _backup_dir() / name
    if not backup_file.exists():
        return JsonResponse({'detail': f'备份文件不存在：{name}'}, status=404)
    job_id = uuid.uuid4().hex
    t = threading.Thread(target=_run_restore_job, args=(job_id, name), daemon=True)
    t.start()
    return JsonResponse({'job_id': job_id, 'message': '恢复任务已启动'})


@csrf_exempt
def backup_restore_status(request):
    """查询恢复任务状态：running / success / error。"""
    job_id = request.GET.get('job_id', '').strip()
    if not job_id:
        return JsonResponse({'detail': '请提供 job_id'}, status=400)
    with _restore_jobs_lock:
        job = _restore_jobs.get(job_id)
    if not job:
        return JsonResponse({'status': 'running', 'detail': '任务尚未开始'})
    return JsonResponse(job)

@csrf_exempt
def backup_delete(request):
    try:
        data = json.loads(request.body) if request.body else {}
        name = data.get('name', '').strip()
    except Exception:
        name = ''
    if not name:
        return JsonResponse({'detail': '请提供备份文件名'}, status=400)
    backup_file = _backup_dir() / name
    if not backup_file.exists():
        return JsonResponse({'detail': f'备份文件不存在：{name}'}, status=404)
    backup_file.unlink()
    return JsonResponse({'message': f'已删除 {name}'})
