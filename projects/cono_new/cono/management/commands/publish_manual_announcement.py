"""发布「新版网站使用手册」公告。

在 NAS 上执行一次即可，写入的是 settings 里配置的正式库（192.168.1.201）。
按标题幂等：重复执行只更新内容，不会产生重复公告。

    python manage.py publish_manual_announcement
    python manage.py publish_manual_announcement --new-url http://192.168.1.202:8001
    python manage.py publish_manual_announcement --dry-run
"""
from django.core.management.base import BaseCommand, CommandError

from cono import models

TITLE = '新版网站使用手册已发布，手机上也能看'

CONTENT = """新版网站使用手册已经整理完成。内容包括登录、界面导航、公告通知、合同、回款与发票、生产发货、售后服务、售后流转、用户权限和系统工具，共 14 章，配 24 张实机截图。遇到不会操作的地方，先翻手册，多数问题都能找到步骤。

一、手册在哪里

文件为 Word 格式，文件名「新版网站使用手册.docx」，存放在公司 NAS 的共享目录，也可以向信息管理员索取。

二、手机上怎么看

手机连上公司 WiFi，在浏览器地址栏输入：

{new_url}

这是新版系统的地址，手机屏幕会自动适配，点左上角的菜单按钮可以展开侧边菜单。手册里的截图和步骤，对着手机操作同样能找到位置。

如果只想在手机上看手册文件本身，把 docx 发到微信「文件传输助手」，用 WPS 打开即可，排版和电脑上一致。

三、看手册的建议

1. 第一次使用新版，先看第二章「登录与退出」和第三章「界面导航」，把界面认全。
2. 日常办业务直接翻对应章节：签合同看第五章，回款和开票看第六章，生产和发货看第七章。
3. 找不到菜单时看附录 A「菜单速查表」，里面列了每个菜单的路径和常用操作。
4. 从老版过渡过来的同事，看附录 B「模块与老版对照」，能快速找到对应位置。

四、遇到问题

手册第十四章列了常见问题，可以先自查。如果手册里也没有答案，请记下操作时间、所在页面和页面提示的原文，反馈给信息管理员，便于快速定位。

新版系统：{new_url}
老版系统：{old_url}"""


class Command(BaseCommand):
    help = '发布新版网站使用手册公告（按标题幂等，重复执行只更新内容）'

    def add_arguments(self, parser):
        parser.add_argument('--title', default=TITLE, help='公告标题，同时作为幂等键')
        parser.add_argument('--new-url', default='http://192.168.1.202:8001',
                            help='新版系统地址，写在公告正文里')
        parser.add_argument('--old-url', default='http://192.168.1.202:8000',
                            help='老版系统地址，写在公告正文里')
        parser.add_argument('--publisher', default=None,
                            help='发布人账号，默认取第一个管理员')
        parser.add_argument('--kind', type=int, default=1, choices=[1, 2],
                            help='1=公告，2=通知')
        parser.add_argument('--top', action='store_true', help='置顶')
        parser.add_argument('--dry-run', action='store_true', help='只打印不写库')

    def handle(self, *args, **options):
        content = CONTENT.format(new_url=options['new_url'], old_url=options['old_url'])

        publisher = self._resolve_publisher(options['publisher'])

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('--dry-run：以下内容不会写入数据库\n'))
            self.stdout.write(f'标题：{options["title"]}')
            self.stdout.write(f'发布人：{publisher.username}')
            self.stdout.write(f'类型：{"公告" if options["kind"] == 1 else "通知"}'
                              f'  置顶：{"是" if options["top"] else "否"}')
            self.stdout.write(f'字数：{len(content)}\n')
            self.stdout.write(content)
            return

        obj, created = models.Announcement.objects.get_or_create(
            title=options['title'],
            defaults={
                'content': content,
                'kind': options['kind'],
                'is_top': options['top'],
                'is_active': True,
                'publisher': publisher,
            },
        )

        if not created:
            obj.content = content
            obj.kind = options['kind']
            obj.is_top = options['top']
            obj.is_active = True
            obj.save()
            self.stdout.write(self.style.SUCCESS(f'已更新公告 id={obj.id}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已发布公告 id={obj.id}'))

        self.stdout.write(f'标题：{obj.title}')
        self.stdout.write(f'发布人：{publisher.username}  字数：{len(obj.content)}')

    def _resolve_publisher(self, username):
        if username:
            user = models.User.objects.filter(username=username).first()
            if user is None:
                raise CommandError(f'发布人账号不存在：{username}')
            return user

        user = models.User.objects.filter(role='admin').order_by('id').first()
        if user is None:
            raise CommandError('库里没有管理员账号，请用 --publisher 指定发布人')
        return user
