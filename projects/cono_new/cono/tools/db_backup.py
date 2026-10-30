"""数据库备份/还原的公共逻辑，网页按钮和每日自动备份命令共用。"""
import glob
import os
import subprocess

from django.conf import settings
from django.utils import timezone

AUTO_PREFIX = 'auto'


def backup_dir():
    return os.path.join(settings.BASE_DIR, 'backups')


def db_config():
    """当前数据库连接参数。"""
    config = settings.DATABASES['default']
    return {
        'user': config['USER'],
        'password': config['PASSWORD'],
        'name': config['NAME'],
        'host': config.get('HOST') or 'localhost',
        'port': str(config.get('PORT') or '3306'),
    }


def no_ssl_args(client):
    """MariaDB 客户端默认校验服务端证书，连自签证书的 MySQL 会报 TLS/SSL error，
    这里统一关闭 SSL；Oracle 的 mysql/mysqldump 不支持 --skip-ssl，改用 --ssl-mode。"""
    try:
        result = subprocess.run([client, '--version'], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10)
        version = (result.stdout or b'').decode('utf-8', 'replace').lower()
    except (OSError, subprocess.SubprocessError):
        version = ''
    if 'mariadb' in version:
        return ['--skip-ssl']
    return ['--ssl-mode=DISABLED']


def error_message(stderr, password):
    message = (stderr or b'').decode('utf-8', 'replace').strip()
    if password:
        message = message.replace(password, '******')
    return message or '命令执行失败，请查看容器日志'


def create_backup(prefix=''):
    """执行 mysqldump 生成备份文件，返回文件路径；失败抛 RuntimeError 并清理残缺文件。"""
    config = db_config()
    directory = backup_dir()
    os.makedirs(directory, exist_ok=True)
    stamp = timezone.localtime().strftime('%Y%m%d%H%M')
    suffix = '_{}'.format(prefix) if prefix else ''
    backup_file = os.path.join(directory, '{}{}{}.sql'.format(config['name'], suffix, stamp))
    cmd = [
        'mysqldump',
        '--no-tablespaces',
    ] + no_ssl_args('mysqldump') + [
        '-u', config['user'],
        '-p' + config['password'],
        '-h', config['host'],
        '-P', config['port'],
        config['name'],
    ]
    try:
        with open(backup_file, 'wb') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
        if result.returncode != 0 or os.path.getsize(backup_file) == 0:
            raise RuntimeError(error_message(result.stderr, config['password']))
    except (OSError, subprocess.SubprocessError, RuntimeError):
        if os.path.exists(backup_file):
            os.remove(backup_file)
        raise
    return backup_file


def restore_backup(sql_file):
    """把备份文件导入数据库，失败抛 RuntimeError。"""
    config = db_config()
    cmd = [
        'mysql',
    ] + no_ssl_args('mysql') + [
        '-u', config['user'],
        '-p' + config['password'],
        '-h', config['host'],
        '-P', config['port'],
        config['name'],
    ]
    try:
        with open(sql_file, 'rb') as f:
            result = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(error_message(result.stderr, config['password']))
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        raise RuntimeError(str(exc))


def auto_backup_files():
    """自动备份产生的文件，按时间从早到晚排列。"""
    pattern = os.path.join(backup_dir(), '{}_auto*.sql'.format(db_config()['name']))
    return sorted(glob.glob(pattern))


def auto_backup_exists(day=None):
    day = day or timezone.localdate()
    pattern = os.path.join(backup_dir(), '{}_auto{}*.sql'.format(db_config()['name'], day.strftime('%Y%m%d')))
    return bool(glob.glob(pattern))


def auto_backup_hour():
    return int(getattr(settings, 'DB_BACKUP_HOUR', 11))


def auto_backup_due(now=None):
    """是否到了当天的自动备份时间，且今天还没备份过。"""
    now = now or timezone.localtime()
    if now.hour < auto_backup_hour():
        return False
    return not auto_backup_exists(now.date())


def cleanup_old_auto_backups(keep=None):
    """只保留最近 keep 份自动备份，返回被删除的文件列表。"""
    if keep is None:
        keep = int(getattr(settings, 'DB_BACKUP_KEEP', 30))
    if keep <= 0:
        return []
    files = auto_backup_files()
    stale = files[:-keep] if len(files) > keep else []
    for path in stale:
        os.remove(path)
    return stale


def latest_auto_backup():
    """最近一次自动备份的文件路径，没有则返回 None。"""
    files = auto_backup_files()
    return files[-1] if files else None
