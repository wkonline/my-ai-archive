from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cono import models

DEFAULT_HOURS = 24


class Command(BaseCommand):
    help = '清理未绑定到公告的草稿附件（上传后放弃的）'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=DEFAULT_HOURS,
                            help='超过多少小时未绑定即删除，默认 {}'.format(DEFAULT_HOURS))
        parser.add_argument('--dry-run', action='store_true', help='只统计不删除')

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        stale = models.AnnouncementAttachment.objects.filter(
            announcement__isnull=True, create_time__lt=cutoff)
        total = 0
        for att in stale:
            if not options['dry_run']:
                att.file.delete(save=False)
                att.delete()
            total += 1
        prefix = '[dry-run] ' if options['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            '{}清理草稿附件 {} 个'.format(prefix, total)))
