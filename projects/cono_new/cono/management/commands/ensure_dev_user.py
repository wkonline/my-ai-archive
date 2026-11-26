"""本地开发用：确保 SQLite 测试库里有可登录的账号。

只在 USE_SQLITE 模式下由 deploy/dev.sh 调用。密码哈希用 settings.SECRET_KEY 计算，
与老系统 cono.tools.encrypt.md5 完全一致，所以同一个账号在新旧两套系统都能登录。
"""
from django.core.management.base import BaseCommand
from django.conf import settings

from cono import models
from cono.tools.encrypt import md5


class Command(BaseCommand):
    help = '在空的 SQLite 测试库里创建部门与管理员账号（已存在则跳过）'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--department', default='管理部')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        if models.User.objects.filter(username=username).exists():
            self.stdout.write(f'账号 {username} 已存在，跳过')
            return

        department, _ = models.Department.objects.get_or_create(
            title=options['department'],
        )
        models.User.objects.create(
            username=username,
            password=md5(password),
            role='admin',
            id_number=f'LOCAL{username}'[:18],
            phone='13800000000',
            address='本地开发',
            department=department,
            create_date='2024-01-01',
        )
        salt_hint = settings.SECRET_KEY[:12]
        self.stdout.write(self.style.SUCCESS(
            f'已创建本地账号 {username} / {password}（盐 {salt_hint}...）'
        ))
