import glob
import os
import time

from django.core.management.base import BaseCommand

from cono.tools import db_backup


# 备份文件名兼容两种命名：老版 cono_{timestamp}.sql，新版 cono{timestamp}.sql
BACKUP_GLOB_OLD = os.path.join(db_backup.backup_dir(), 'cono_*.sql')
BACKUP_GLOB_NEW = os.path.join(db_backup.backup_dir(), 'cono*.sql')


def _today_backups():
    """返回今天所有 cono*.sql 文件名（不区分是否有下划线）。"""
    today = time.strftime('%Y%m%d')
    results = []
    for pattern in (BACKUP_GLOB_OLD, BACKUP_GLOB_NEW):
        for f in glob.glob(pattern):
            name = os.path.basename(f)
            # 提取时间戳部分：去掉 cono_/ 前缀和 .sql 后缀
            without_prefix = name[len('cono'):]  # 去掉 "cono"
            ts_start = 1 if without_prefix.startswith('_') else 0
            ts = without_prefix[ts_start:ts_start + 8]
            if ts == today:
                results.append(name)
    return sorted(set(results))


def _cleanup_by_days(days):
    """删除早于 days 天的所有 cono*.sql 备份文件，返回被删数量。"""
    import datetime as _dt
    cutoff = (_dt.datetime.now() - _dt.timedelta(days=days)).timestamp()
    removed = 0
    seen = set()
    for pattern in (BACKUP_GLOB_OLD, BACKUP_GLOB_NEW):
        for f in glob.glob(pattern):
            if f in seen:
                continue
            seen.add(f)
            if os.path.getmtime(f) < cutoff:
                os.remove(f)
                removed += 1
    return removed


class Command(BaseCommand):
    help = '备份 MySQL 数据库，并清理超过保留天数的旧备份。每天 23:00 自动执行。'

    def add_arguments(self, parser):
        parser.add_argument('--if-due', action='store_true',
                            help='只在到达每日备份时间（默认 23 点）且今天还没备份时执行')
        parser.add_argument('--force', action='store_true', help='忽略时间判断，直接备份')
        parser.add_argument('--keep', type=int, default=None,
                            help='按份数保留（兼容旧配置），与 --retention-days 互斥')
        parser.add_argument('--retention-days', type=int, default=60,
                            help='按天数保留（默认 60 天），超出自动删除。优先级高于 --keep')
        parser.add_argument('--verbose', action='store_true', help='打印跳过原因')

    def handle(self, *args, **options):
        if options['if_due'] and not options['force']:
            now = db_backup.timezone.localtime()
            backup_hour = int(os.environ.get('DJANGO_DB_BACKUP_HOUR', '23'))
            today_files = _today_backups()
            if today_files:
                if options['verbose']:
                    self.stdout.write(f'跳过：今天已有备份 {today_files[-1]}')
                return
            if now.hour < backup_hour:
                if options['verbose']:
                    self.stdout.write(
                        f'跳过：未到备份时间（当前 {now.hour:02d}:00，设定 {backup_hour}:00）'
                    )
                return

        try:
            backup_file = db_backup.create_backup(prefix='')
        except RuntimeError as exc:
            self.stderr.write(f'备份失败：{exc}')
            raise SystemExit(1)

        size_kb = os.path.getsize(backup_file) / 1024
        self.stdout.write(f'备份完成：{os.path.basename(backup_file)}  ({size_kb:.1f} KB)')

        # 清理过期备份
        if options['keep'] is not None and options['retention_days'] == 60:
            removed = db_backup.cleanup_old_auto_backups(options['keep'])
            if removed:
                self.stdout.write(
                    f'已清理 {len(removed)} 个过期自动备份（保留最近 {options["keep"]} 份）'
                )
        else:
            days = options['retention_days']
            removed = _cleanup_by_days(days)
            if removed:
                self.stdout.write(f'已删除 {removed} 个超过 {days} 天的旧备份')
            else:
                self.stdout.write(f'无需清理，所有备份均在 {days} 天内')
