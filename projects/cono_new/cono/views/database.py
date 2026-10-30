import datetime
import os

from django.conf import settings
from django.shortcuts import render

from cono.tools import db_backup


def _backup_context(title):
    """备份页公共信息：备份目录、每日自动备份状态。"""
    latest = db_backup.latest_auto_backup()
    latest_info = None
    if latest:
        latest_info = {
            'name': os.path.basename(latest),
            'time': datetime.datetime.fromtimestamp(os.path.getmtime(latest)).strftime('%Y-%m-%d %H:%M'),
            'size': os.path.getsize(latest),
        }
    return {
        'title': title,
        'backup_dir': db_backup.backup_dir(),
        'auto_backup_hour': db_backup.auto_backup_hour(),
        'auto_backup_keep': int(getattr(settings, 'DB_BACKUP_KEEP', 30)),
        'auto_backup_count': len(db_backup.auto_backup_files()),
        'auto_backup_latest': latest_info,
        'auto_backup_done_today': db_backup.auto_backup_exists(),
    }


def backup_database(request):
    title = '数据库备份'
    context = _backup_context(title)
    if request.method == 'POST':
        try:
            context['backup_file'] = db_backup.create_backup()
        except RuntimeError as exc:
            context['error'] = '备份失败：{}'.format(exc)
            return render(request, 'database/backup.html', context)
        return render(request, 'success.html', {'title': title, 'url_path': '/database/backup/list/'})
    return render(request, 'database/backup.html', context)


def restore_database(request):
    title = '数据库还原'
    context = {'title': title}
    if request.method == 'POST':
        uploaded_file = request.FILES.get('backup_file')
        if uploaded_file is None:
            context['error'] = '还原失败：请先选择备份文件'
            return render(request, 'database/restore.html', context)

        temp_file = os.path.join(settings.BASE_DIR, 'temp_backup.sql')
        with open(temp_file, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        try:
            db_backup.restore_backup(temp_file)
        except RuntimeError as exc:
            context['error'] = '还原失败：{}'.format(exc)
            return render(request, 'database/restore.html', context)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return render(request, 'success.html', {'title': title, 'url_path': '/database/restore/list/'})
    return render(request, 'database/restore.html', context)
