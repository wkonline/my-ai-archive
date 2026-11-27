"""首页聚合接口：一次性返回老版首页所需的指标、最近列表、图表数据。"""
import datetime

from django.db.models import Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.core import models
from api.core.permissions import get_effective_permissions


def _amount(queryset, field='amount'):
    return queryset.aggregate(total=Sum(field))['total'] or 0


# 2013–2022 年度电源装配数量：早年数据未进生产计划系统，按历史台账硬编码。
# 2023 年起系统内有完整计划记录，改从 Plan.quantity 汇总，不再维护这张表。
ASSEMBLY_HISTORY = {
    2013: 42, 2014: 43, 2015: 44, 2016: 71, 2017: 81,
    2018: 53, 2019: 62, 2020: 44, 2021: 93, 2022: 122,
}
ASSEMBLY_PLAN_FROM_YEAR = 2023


class HomeView(APIView):
    """参照老版 cono/views/index.py home() 实现，返回首页数据。

    各模块按用户权限门控：未授权的模块不查询、不返回数据，与老版
    cono/views/index.py:41-53 的 can_xxx 语义保持一致。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perms = get_effective_permissions(request.user)
        # admin 的 get_effective_permissions 返回 None，代表全部放行
        def can(*codes):
            return perms is None or any(c in perms for c in codes)

        can_contract = can('contract_list')
        can_collection = can('collection_list')
        can_invoice = can('invoice_list')
        can_plan = can('plan_list')
        can_customer = can('customer_list')
        can_service = can('service_list')
        can_servicedetail = can('servicedetail_list')
        can_return_product = can('return_product_list')
        can_delivery = can('delivery_list')
        can_flow_out = can('flow_out_list')
        can_flow_return = can('flow_return_list')
        can_chart = can('chart_list', 'chart_bar', 'chart_bar2',
                        'chart_pie', 'chart_line', 'highcharts')

        today = datetime.date.today()
        month_start = today.replace(day=1)
        next_month = (
            datetime.date(today.year + 1, 1, 1) if today.month == 12
            else datetime.date(today.year, today.month + 1, 1)
        )
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        quarter_start = datetime.date(today.year, quarter_month, 1)
        quarter_end = (
            datetime.date(today.year + 1, 1, 1) if quarter_month == 10
            else datetime.date(today.year, quarter_month + 3, 1)
        )
        year_start = datetime.date(today.year, 1, 1)
        next_year = datetime.date(today.year + 1, 1, 1)

        # 指标
        year_contract = (
            models.Contract.objects.filter(
                is_delete=False,
                date__gte=year_start, date__lt=next_year,
            ).aggregate(total_count=Count('id'), total_amount=Sum('total_price'))
            if can_contract else {'total_count': 0, 'total_amount': 0}
        )
        month_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=month_start, date__lt=next_month,
        ) if can_collection else models.Collection.objects.none()
        quarter_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=quarter_start, date__lt=quarter_end,
        ) if can_collection else models.Collection.objects.none()
        month_invoices = models.Invoice.objects.filter(
            is_delete=False,
            date__gte=month_start, date__lt=next_month,
        ) if can_invoice else models.Invoice.objects.none()
        month_deliveries = models.ProductDelivery.objects.filter(
            is_delete=False,
            date__gte=month_start, date__lt=next_month,
        ) if can_delivery else models.ProductDelivery.objects.none()
        # 待完工以 completed_status 为准：它是界面显示的状态，也是发货/派单流程
        # 唯一维护的字段。completed 布尔值只在发货流程里一并写入，计划表单改状态
        # 时不跟手，拿它计数会把「已完成」的计划算成待完工。
        pending_plan_qs = models.Plan.objects.filter(
            is_delete=False,
            completed_status__in=(1, 2),
            contract__is_delete=False,
        ) if can_plan else models.Plan.objects.none()
        pending_plans = pending_plan_qs.count()
        overdue_plans = pending_plan_qs.filter(delivery_date__lt=today).count()
        customer_count = models.Customer.objects.filter(
            is_delete=False,
        ).count() if can_customer else 0

        # 最近列表
        recent_contracts = models.Contract.objects.filter(
            is_delete=False,
        ).select_related('customer', 'customer__saler').order_by('-date', '-id')[:6] if can_contract else []
        recent_collections = models.Collection.objects.filter(
            is_delete=False,
        ).select_related('customer', 'contract').order_by('-date', '-id')[:6] if can_collection else []
        recent_invoices = models.Invoice.objects.filter(
            is_delete=False,
        ).select_related(
            'customer', 'contract',
        ).order_by('-date', '-id')[:6] if can_invoice else []
        # 未完工计划按交货日期排序，逾期的排前面：它们最需要关注，
        # 原先只取「今天起 60 天内」，逾期计划整批消失，卡片说有待完工、
        # 表格却空着，看着像数据丢了。
        upcoming_plans = pending_plan_qs.select_related(
            'contract', 'productcategory', 'product',
        ).order_by('delivery_date', 'id')[:6] if can_plan else []
        recent_services = models.Service.objects.filter(
            is_delete=False,
        ).select_related('customer', 'productcategory', 'product').order_by('-date', '-id')[:6] if can_service else []
        recent_servicedetails = models.ServiceDetail.objects.filter(
            is_delete=False,
        ).select_related(
            'customer', 'service', 'product', 'repairman',
        ).order_by('-repair_date', '-id')[:6] if can_servicedetail else []
        recent_return_products = models.ReturnProduct.objects.filter(
            is_delete=False,
        ).select_related('customer', 'service', 'user').order_by('-date', '-id')[:6] if can_return_product else []
        recent_flow_outs = models.FlowOut.objects.filter(
            is_delete=False,
        ).select_related(
            'archive', 'archive__productcategory', 'customer',
        ).order_by('-ship_date', '-id')[:6] if can_flow_out else []
        recent_flow_returns = models.FlowReturn.objects.filter(
            is_delete=False,
        ).select_related(
            'flow_out', 'flow_out__customer', 'flow_out__archive',
        ).order_by('-actual_return_date', '-id')[:6] if can_flow_return else []

        # 图表：年度合同业绩柱状图 + 客户销售占比饼图
        if can_chart:
            year_labels = [str(y) for y in range(2013, today.year + 1)]
            year_amounts = []
            for year_label in year_labels:
                total = models.Contract.objects.filter(
                    is_delete=False,
                    date__year=int(year_label),
                ).aggregate(total=Sum('total_price'))['total'] or 0
                year_amounts.append(float(total))

            customer_sales = models.Contract.objects.filter(
                is_delete=False,
                date__gte=year_start, date__lt=next_year,
            ).values('customer__company_name').annotate(
                total=Sum('total_price')).order_by('-total')
            top_sales = list(customer_sales[:5])
            total_amount = sum(float(item['total'] or 0) for item in customer_sales)
            top_amount = sum(float(item['total'] or 0) for item in top_sales)
            pie_labels = [item['customer__company_name'] for item in top_sales]
            pie_values = [float(item['total'] or 0) for item in top_sales]
            if total_amount - top_amount > 0:
                pie_labels.append('其他')
                pie_values.append(round(total_amount - top_amount, 2))
        else:
            year_labels, year_amounts = [], []
            pie_labels, pie_values = [], []

        # 电源装配数量：早年取历史台账，2023 年起按生效日期从生产计划汇总。
        # 口径与生产计划列表的年度数量一致（Plan.quantity + effective_date + 未删除）。
        assembly_labels = [str(y) for y in range(2013, today.year + 1)]
        assembly_values = []
        for label in assembly_labels:
            year = int(label)
            if year < ASSEMBLY_PLAN_FROM_YEAR:
                assembly_values.append(ASSEMBLY_HISTORY.get(year, 0))
            else:
                total = models.Plan.objects.filter(
                    is_delete=False,
                    effective_date__gte=datetime.date(year, 1, 1),
                    effective_date__lt=datetime.date(year + 1, 1, 1),
                ).aggregate(total=Sum('quantity'))['total'] or 0
                assembly_values.append(total)

        def _fmt(d):
            return d.strftime('%Y-%m-%d') if d else ''

        return Response({
            'today': today.strftime('%Y-%m-%d'),
            'year': today.year,
            # 前端据此隐藏无权限的卡片/图表/表格，避免出现空区块或点了报无权限
            'visible': {
                'contract': can_contract,
                'collection': can_collection,
                'invoice': can_invoice,
                'plan': can_plan,
                'customer': can_customer,
                'service': can_service,
                'servicedetail': can_servicedetail,
                'return_product': can_return_product,
                'delivery': can_delivery,
                'flow_out': can_flow_out,
                'flow_return': can_flow_return,
                'chart': can_chart,
            },
            'metrics': {
                'year_contract_count': year_contract['total_count'] or 0,
                'year_contract_amount': float(year_contract['total_amount'] or 0),
                'month_collection_amount': float(_amount(month_collections)),
                'month_collection_count': month_collections.count(),
                'quarter_collection_amount': float(_amount(quarter_collections)),
                'quarter_collection_count': quarter_collections.count(),
                'month_invoice_amount': float(_amount(month_invoices)),
                'month_invoice_count': month_invoices.count(),
                'month_delivery_count': month_deliveries.count(),
                'month_delivery_qty': month_deliveries.aggregate(total=Sum('quantity'))['total'] or 0,
                'pending_plans': pending_plans,
                'overdue_plans': overdue_plans,
                'customer_count': customer_count,
            },
            'recent_contracts': [{
                'id': c.id,
                'contract_number': c.contract_number,
                'customer_name': c.customer.company_name if c.customer else '',
                'saler_name': c.customer.saler.username if c.customer and c.customer.saler else '',
                'date': _fmt(c.date),
                'total_price': float(c.total_price or 0),
            } for c in recent_contracts],
            'upcoming_plans': [{
                'id': p.id,
                'contract_id': p.contract_id,
                'contract_number': p.contract.contract_number if p.contract else '',
                'productcategory_name': p.productcategory.name if p.productcategory else '',
                'product_model': p.product.model if p.product else '',
                'delivery_date': _fmt(p.delivery_date),
                # 逾期未完工：交货日期已过，前端据此标红提示
                'is_overdue': bool(p.delivery_date and p.delivery_date < today),
                'completed_status': p.completed_status,
                'completed_status_display': p.get_completed_status_display(),
            } for p in upcoming_plans],
            'recent_collections': [{
                'id': c.id,
                'customer_name': c.customer.company_name if c.customer else '',
                'contract_id': c.contract_id,
                'contract_number': c.contract.contract_number if c.contract else '',
                'date': _fmt(c.date),
                'amount': float(c.amount or 0),
            } for c in recent_collections],
            'recent_invoices': [{
                'id': i.id,
                'customer_name': i.customer.company_name if i.customer else '',
                'contract_id': i.contract_id,
                'contract_number': i.contract.contract_number if i.contract else '',
                'date': _fmt(i.date),
                'amount': float(i.amount or 0),
            } for i in recent_invoices],
            'recent_services': [{
                'id': s.id,
                'customer_name': s.customer.company_name if s.customer else '',
                'service_number': s.service_number,
                'product_model': s.product.model if s.product else '',
                'date': _fmt(s.date),
                'warranty_end': s.warranty_end,
                'warranty_end_display': s.get_warranty_end_display(),
            } for s in recent_services],
            'recent_servicedetails': [{
                'id': sd.id,
                'customer_name': sd.customer.company_name if sd.customer else '',
                'service_number': sd.service.service_number if sd.service else '',
                'product_model': sd.product.model if sd.product else '',
                'repairman_name': sd.repairman.username if sd.repairman else '',
                'repair_date': _fmt(sd.repair_date),
            } for sd in recent_servicedetails],
            'recent_return_products': [{
                'id': r.id,
                'customer_name': r.customer.company_name if r.customer else '',
                'service_number': r.service.service_number if r.service else '',
                'user_name': r.user.username if r.user else '',
                'date': _fmt(r.date),
            } for r in recent_return_products],
            'recent_flow_outs': [{
                'id': f.id,
                'flow_number': f.flow_number,
                'archive_serial': f.archive.serial_number if f.archive else '',
                'productcategory_name': (
                    f.archive.productcategory.name if f.archive and f.archive.productcategory else ''
                ),
                'product_model': (
                    f.archive.product.model if f.archive and f.archive.product else ''
                ),
                'customer_name': f.customer.company_name if f.customer else '',
                'ship_date': _fmt(f.ship_date),
                'status': f.status,
                'status_display': f.get_status_display(),
            } for f in recent_flow_outs],
            'recent_flow_returns': [{
                'id': r.id,
                'flow_number': r.flow_out.flow_number if r.flow_out else '',
                'archive_serial': r.snapshot_serial,
                'productcategory_name': (
                    r.flow_out.archive.productcategory.name
                    if r.flow_out and r.flow_out.archive and r.flow_out.archive.productcategory else ''
                ),
                'customer_name': (
                    r.flow_out.customer.company_name if r.flow_out and r.flow_out.customer else ''
                ),
                'actual_return_date': _fmt(r.actual_return_date),
                'is_board_swapped': r.is_board_swapped,
                'result_status_display': r.get_result_status_display(),
            } for r in recent_flow_returns],
            'charts': {
                'year_labels': year_labels,
                'year_values': year_amounts,
                'pie_labels': pie_labels,
                'pie_values': pie_values,
                'assembly_labels': assembly_labels,
                'assembly_values': assembly_values,
                'assembly_plan_from_year': ASSEMBLY_PLAN_FROM_YEAR,
            },
        })
