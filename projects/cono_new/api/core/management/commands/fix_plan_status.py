"""一次性修正生产计划「生产状态」历史数据。

背景：BaseModelViewSet.destroy 长期不调用 perform_destroy，导致删除发货记录
后从不重算计划状态。线上可能已积累一批状态不准的记录。

默认只报告不写库，确认无误后再加 --apply 执行。

    python manage.py fix_plan_status              # 只列出会改动的记录
    python manage.py fix_plan_status --apply      # 实际写库
    python manage.py fix_plan_status --apply --include-completed
                                                  # 连已完成的记录一起重算
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from api.core import models
from api.core.views.production import _derive_plan_status


class Command(BaseCommand):
    help = '按发货量与任务单修正生产计划的生产状态（默认只报告，不写库）'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='实际写库。不加此参数时只打印将要改动的记录。')
        parser.add_argument('--include-completed', action='store_true',
                            help='连当前状态为已完成的记录也一起重算（默认跳过）')
        parser.add_argument('--limit', type=int, default=50,
                            help='预览时最多打印多少条明细，默认 50')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        include_completed = options['include_completed']
        limit = options['limit']

        qs = models.Plan.objects.filter(is_delete=False).select_related(
            'contract', 'product', 'productcategory').order_by('id')
        if not include_completed:
            qs = qs.exclude(completed_status=3)

        changes = []
        for plan in qs.iterator():
            # 无任何任务单与发货记录时，计划本就该是待生产
            status, completed = _derive_plan_status(plan) or (1, False)
            if (plan.completed_status, plan.completed) != (status, completed):
                changes.append((plan, status, completed))

        total_plans = qs.count()
        if not changes:
            self.stdout.write(self.style.SUCCESS(
                '检查了 {} 条生产计划，状态均正确，无需修正。'.format(total_plans)))
            return

        self.stdout.write('检查了 {} 条生产计划，发现 {} 条需要修正：'.format(
            total_plans, len(changes)))
        self.stdout.write('')
        for plan, status, completed in changes[:limit]:
            number = plan.contract.contract_number if plan.contract else ''
            if plan.is_temp_plan:
                number = plan.contract_reserve or '临时计划'
            self.stdout.write('  计划#{id} {number} / {product}: {old} -> {new}{done}'.format(
                id=plan.id, number=number,
                product=plan.product.model if plan.product else '',
                old=plan.get_completed_status_display(),
                new=dict(models.Plan.STATUS_CHOICES).get(status, status),
                done='（同时修正完结标记）'
                     if plan.completed != completed else ''))
        if len(changes) > limit:
            self.stdout.write('  ... 另有 {} 条未显示（--limit 可调整）'.format(
                len(changes) - limit))

        if not apply_changes:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                '当前为预览模式，未修改任何数据。确认无误后加 --apply 执行。'))
            return

        with transaction.atomic():
            for plan, status, completed in changes:
                plan.completed_status = status
                plan.completed = completed
                plan.save(update_fields=['completed_status', 'completed', 'update_time'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            '已修正 {} 条生产计划的生产状态。'.format(len(changes))))
