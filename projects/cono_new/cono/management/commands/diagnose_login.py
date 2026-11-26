"""诊断登录失败：确认连的是哪个库、库里密码是什么格式、当前盐能否匹配。

用法：
    python manage.py diagnose_login <用户名> [密码] --settings=local_test_settings

省略密码时会交互输入（不回显），避免密码留在 shell 历史里。
省略用户名时只列出库中现有用户。
"""
import hashlib
import getpass

from django.conf import settings
from django.core.management.base import BaseCommand

from cono import models


def md5(salt, data):
    h = hashlib.md5(salt.encode('utf-8'))
    h.update(data.encode('utf-8'))
    return h.hexdigest()


def salt_fp(salt):
    """盐的指纹，用于跨进程比较而不暴露盐本身。"""
    return hashlib.md5(salt.encode('utf-8')).hexdigest()[:8]


class Command(BaseCommand):
    help = '诊断用户名密码错误：检查数据库、密码格式与盐值'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?')
        parser.add_argument('password', nargs='?')

    def handle(self, *args, **options):
        username = options['username']
        db = settings.DATABASES['default']

        self.stdout.write(f'数据库    : {db["ENGINE"]} / {db["NAME"]}')
        self.stdout.write(f'当前 SECRET_KEY : {settings.SECRET_KEY[:16]}...')
        self.stdout.write(f'当前 SECRET_KEY 指纹: {salt_fp(settings.SECRET_KEY)}')
        legacy = getattr(settings, 'LEGACY_SECRET_KEY', None)
        if legacy:
            self.stdout.write(f'LEGACY_SECRET_KEY: {legacy[:16]}...')
            self.stdout.write(f'LEGACY_SECRET_KEY 指纹: {salt_fp(legacy)}')

        if not username:
            users = list(models.User.objects.values_list('username', flat=True)[:50])
            self.stdout.write(f'\n库中共 {len(users)} 个用户: ' + ', '.join(users))
            self.stdout.write('用法: manage.py diagnose_login <用户名> [密码]')
            return

        password = options['password']
        if not password:
            password = getpass.getpass('请输入该账号的密码（不回显）: ')

        user = models.User.objects.filter(username=username).first()
        if not user:
            self.stdout.write(self.style.ERROR(f'\n库中没有用户 {username}'))
            self.stdout.write('库里现有用户: '
                              + ', '.join(models.User.objects.values_list('username', flat=True)[:20]))
            return

        stored = user.password or ''
        self.stdout.write(f'\n用户 {username} 的 password 字段: {stored}')

        if len(stored) == 32 and all(c in '0123456789abcdef' for c in stored):
            self.stdout.write('格式判断: 32 位十六进制 -> md5 哈希（老系统正常格式）')
        else:
            self.stdout.write(self.style.WARNING(
                '格式判断: 不是 md5 -> 明文或其它格式。'
                '老系统只比对 md5，因此必定登录失败；新 API 有明文兜底才能登。'))

        self.stdout.write('\n各盐值算出的哈希:')
        candidates = [
            ('当前 SECRET_KEY', settings.SECRET_KEY),
            ('生产盐 nas-cono-deploy-key-2026', 'nas-cono-deploy-key-2026'),
            ('开发默认盐', 'django-insecure-$_+6ouqgn0hxgt19h&!1yh@^=@@x4xnzxg!zb=vyeg513kv$(j'),
        ]
        if legacy:
            candidates.append(('LEGACY_SECRET_KEY', legacy))

        matched = None
        for label, salt in candidates:
            h = md5(salt, password)
            hit = (h == stored)
            if hit and matched is None:
                matched = label
            self.stdout.write(f'  {"✓" if hit else " "} {label}: {h}')

        self.stdout.write('')
        # 登录侧按候选盐列表逐个比对（cono/tools/password.py），命中任一即可登录
        if matched:
            self.stdout.write(self.style.SUCCESS(
                f'库中哈希由「{matched}」生成，已包含在候选盐列表中，可以正常登录。\n'
                '若该端口仍登录失败，说明它跑的是旧代码或旧盐的残留进程，重启即可。'))
        elif len(stored) == 32:
            self.stdout.write(self.style.ERROR(
                '所有候选盐都对不上，库中哈希由未知盐值生成。\n'
                '可把该盐值加入 cono/tools/password.py 的 candidate_salts()，'
                '或用修改密码功能重设。'))
        else:
            self.stdout.write(self.style.WARNING(
                '库里是明文密码。登录侧已按明文兜底比对，可以登录；\n'
                '但建议用修改密码功能重设为 md5 格式。'))
