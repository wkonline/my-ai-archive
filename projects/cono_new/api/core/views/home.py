"""首页聚合接口：一次性返回老版首页所需的指标、最近列表、图表数据。"""
import datetime
import json
from calendar import monthrange
from decimal import Decimal

from django.db.models import Sum, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.core import models


def _amount(queryset, field='amount'):
    return queryset.aggregate(total=Sum(field))['total'] or 0


class HomeView(APIView):
    """参照老版 cono/views/index.py home() 实现，返回首页全量数据。"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        year_contract = models.Contract.objects.filter(
            is_delete=False,
            date__gte=year_start, date__lt=next_year,
        ).aggregate(total_count=Count('id'), total_amount=Sum('total_price'))
        month_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=month_start, date__lt=next_month,
        )
        quarter_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=quarter_start, date__lt=quarter_end,
        )
        month_invoices = models.Invoice.objects.filter(
            date__gte=month_start, date__lt=next_month,
        )
        month_deliveries = models.ProductDelivery.objects.filter(
            is_delete=False,
            date__gte=month_start, date__lt=next_month,
        )
        pending_plans = models.Plan.objects.filter(
            is_delete=False, completed=False,
        ).count()
        customer_count = models.Customer.objects.filter(is_delete=False).count()

        # 最近列表
        recent_contracts = models.Contract.objects.filter(
            is_delete=False,
        ).select_related('customer', 'customer__saler').order_by('-date', '-id')[:6]
        recent_collections = models.Collection.objects.filter(
            is_delete=False,
        ).select_related('customer', 'contract').order_by('-date', '-id')[:6]
        recent_invoices = models.Invoice.objects.select_related(
            'customer', 'contract',
        ).order_by('-date', '-id')[:6]
        upcoming_plans = models.Plan.objects.filter(
            is_delete=False, completed=False,
            delivery_date__gte=today,
            delivery_date__lt=today + datetime.timedelta(days=60),
        ).select_related('contract', 'productcategory', 'product').order_by(
            'delivery_date', 'id')[:6]
        recent_services = models.Service.objects.filter(
            is_delete=False,
        ).select_related('customer', 'productcategory', 'product').order_by('-date', '-id')[:6]
        recent_servicedetails = models.ServiceDetail.objects.filter(
            is_delete=False,
        ).select_related(
            'customer', 'service', 'product', 'repairman',
        ).order_by('-repair_date', '-id')[:6]
        recent_return_products = models.ReturnProduct.objects.filter(
            is_delete=False,
        ).select_related('customer', 'service', 'user').order_by('-date', '-id')[:6]

        # 图表：年度合同业绩柱状图 + 客户销售占比饼图
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

        def _fmt(d):
            return d.strftime('%Y-%m-%d') if d else ''

        return Response({
            'today': today.strftime('%Y-%m-%d'),
            'year': today.year,
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
            'charts': {
                'year_labels': year_labels,
                'year_values': year_amounts,
                'pie_labels': pie_labels,
                'pie_values': pie_values,
            },
        })
