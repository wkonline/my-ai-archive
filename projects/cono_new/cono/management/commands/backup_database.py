import os

from django.core.management.base import BaseCommand

from cono.tools import db_backup


class Command(BaseCommand):
    help = '备份数据库，配合定时任务可实现每天自动备份'

    def add_arguments(self, parser):
        parser.add_argument('--if-due', action='store_true',
                            help='只在到达每日备份时间（默认 11 点）且今天还没备份时执行')
        parser.add_argument('--force', action='store_true', help='忽略时间判断，直接备份')
        parser.add_argument('--keep', type=int, default=None,
                            help='自动备份保留份数，0 表示不清理（默认取 settings.DB_BACKUP_KEEP）')
        parser.add_argument('--verbose', action='store_true', help='打印跳过原因')

    def handle(self, *args, **options):
        if options['if_due'] and not options['force'] and not db_backup.auto_backup_due():
            if options['verbose']:
                self.stdout.write('跳过：未到备份时间或今天已备份')
            return

        try:
            backup_file = db_backup.create_backup(prefix=db_backup.AUTO_PREFIX)
        except RuntimeError as exc:
            self.stderr.write('备份失败：{}'.format(exc))
            raise SystemExit(1)

        self.stdout.write('备份完成：{}（{} 字节）'.format(backup_file, os.path.getsize(backup_file)))

        removed = db_backup.cleanup_old_auto_backups(options['keep'])
        if removed:
            self.stdout.write('已清理 {} 个过期自动备份'.format(len(removed)))
