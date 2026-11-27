from calendar import monthrange
import json
from django.db.models import Q, OuterRef, Exists, Sum
from django.db.models import Count
from cono import models
from django.http import JsonResponse
from django.shortcuts import render
from datetime import date, timedelta

from cono.tools.auth_profile import (
    filter_allowed_menus,
    get_effective_menus,
    get_session_permissions,
    menu_entry_url,
)


def _amount(queryset, field='amount'):
    return queryset.aggregate(total=Sum(field))['total'] or 0




def home(request):
    permissions = get_session_permissions(request.info_dict_role, request.info_dict_useid)
    today = date.today()
    month_start = today.replace(day=1)
    next_month = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = date(today.year, quarter_month, 1)
    quarter_end = (
        date(today.year + 1, 1, 1)
        if quarter_month == 10
        else date(today.year, quarter_month + 3, 1)
    )
    year_start = date(today.year, 1, 1)
    next_year = date(today.year + 1, 1, 1)

    # 先按权限判定各模块是否可见，未授权的模块不做任何查询，
    # 避免无关数据被读取并写入模板上下文。
    can_contract = 'contract_list' in permissions
    can_collection = 'collection_list' in permissions
    can_invoice = 'invoice_list' in permissions
    can_plan = 'plan_list' in permissions
    can_customer = 'customer_list' in permissions
    can_service = 'service_list' in permissions
    can_servicedetail = 'servicedetail_list' in permissions
    can_return_product = 'return_product_list' in permissions
    can_chart = bool(
        {'chart_list', 'chart_bar', 'chart_bar2', 'chart_pie', 'chart_line', 'highcharts'} & permissions
    )

    contract_stats = {'total_count': 0, 'total_amount': 0}
    year_contract_stats = {'total_count': 0, 'total_amount': 0}
    month_collection_amount = month_collection_count = 0
    quarter_collection_amount = quarter_collection_count = 0
    month_invoice_amount = month_invoice_count = 0
    pending_plans = 0
    customer_count = 0
    recent_contracts = []
    recent_collections = []
    recent_invoices = []
    upcoming_plans = []
    recent_services = []
    recent_servicedetails = []
    recent_return_products = []

    if can_contract:
        contract_stats = models.Contract.objects.filter(is_delete=False).aggregate(
            total_count=Count('id'),
            total_amount=Sum('total_price'),
        )
        year_contract_stats = models.Contract.objects.filter(
            is_delete=False,
            date__gte=year_start,
            date__lt=next_year,
        ).aggregate(
            total_count=Count('id'),
            total_amount=Sum('total_price'),
        )
        recent_contracts = models.Contract.objects.filter(is_delete=False).select_related(
            'customer',
            'customer__saler',
        ).order_by('-date', '-id')[:6]

    if can_collection:
        month_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=month_start,
            date__lt=next_month,
        )
        quarter_collections = models.Collection.objects.filter(
            is_delete=False,
            date__gte=quarter_start,
            date__lt=quarter_end,
        )
        month_collection_amount = _amount(month_collections)
        month_collection_count = month_collections.count()
        quarter_collection_amount = _amount(quarter_collections)
        quarter_collection_count = quarter_collections.count()
        recent_collections = models.Collection.objects.filter(is_delete=False).select_related(
            'customer',
            'contract',
        ).order_by('-date', '-id')[:6]

    if can_invoice:
        month_invoices = models.Invoice.objects.filter(
            date__gte=month_start,
            date__lt=next_month,
        )
        month_invoice_amount = _amount(month_invoices)
        month_invoice_count = month_invoices.count()
        recent_invoices = models.Invoice.objects.select_related(
            'customer',
            'contract',
        ).order_by('-date', '-id')[:6]

    if can_plan:
        # 与新版 api/core/views/home.py 同一口径：以 completed_status 为准，
        # 并排除合同已软删的计划。completed 布尔值不跟手，不能用来计数。
        pending_plan_qs = models.Plan.objects.filter(
            is_delete=False,
            completed_status__in=(1, 2),
            contract__is_delete=False,
        )
        pending_plans = pending_plan_qs.count()
        upcoming_plans = pending_plan_qs.select_related(
            'contract',
            'productcategory',
            'product',
        ).order_by('delivery_date', 'id')[:6]

    if can_service:
        recent_services = models.Service.objects.filter(is_delete=False).select_related(
            'customer',
            'productcategory',
            'product',
        ).order_by('-date', '-id')[:6]

    if can_servicedetail:
        recent_servicedetails = models.ServiceDetail.objects.filter(is_delete=False).select_related(
            'customer',
            'service',
            'productcategory',
            'product',
            'repairman',
        ).order_by('-repair_date', '-id')[:6]

    if can_return_product:
        recent_return_products = models.ReturnProduct.objects.filter(is_delete=False).select_related(
            'customer',
            'service',
            'user',
        ).order_by('-date', '-id')[:6]

    if can_customer:
        customer_count = models.Customer.objects.filter(is_delete=False).count()

    user = models.User.objects.filter(id=request.info_dict_useid).first()
    if user:
        menus = get_effective_menus(user)
    else:
        from django.conf import settings
        menus = settings.CONO_MENU.get(request.info_dict_role, [])

    # 只展示当前用户真正有权限访问的入口，避免出现点击后“无权访问”的链接。
    allowed_menus = filter_allowed_menus(menus, permissions)

    icon_rules = (
        ('合同', 'glyphicon-file'),
        ('回款', 'glyphicon-piggy-bank'),
        ('发票', 'glyphicon-list-alt'),
        ('生产', 'glyphicon-cog'),
        ('客户', 'glyphicon-user'),
        ('统计', 'glyphicon-stats'),
        ('售后', 'glyphicon-wrench'),
        ('资料', 'glyphicon-folder-open'),
        ('用户', 'glyphicon-th-list'),
        ('权限', 'glyphicon-lock'),
        ('备份', 'glyphicon-hdd'),
        ('日志', 'glyphicon-time'),
    )
    quick_menus = []
    for item in allowed_menus[:10]:
        icon = 'glyphicon-th-large'
        for keyword, matched_icon in icon_rules:
            if keyword in item.get('title', ''):
                icon = matched_icon
                break
        quick_menus.append({
            'title': item.get('title', ''),
            'url': menu_entry_url(item),
            'icon': icon,
        })

    # 图表数据仅在具备统计权限时才查询
    year_labels = []
    year_amounts = []
    pie_labels = []
    pie_values = []
    if can_chart:
        # 全量年度合同业绩柱状图（从 2013 年开始）
        year_labels = [str(y) for y in range(2013, today.year + 1)]
        for year_label in year_labels:
            total = models.Contract.objects.filter(
                is_delete=False,
                date__year=int(year_label),
            ).aggregate(total=Sum('total_price'))['total'] or 0
            year_amounts.append(float(total))

        # 客户销售占比饼图（仅本年度，取前五名，其余合并为其他）
        customer_sales = models.Contract.objects.filter(
            is_delete=False,
            date__gte=year_start,
            date__lt=next_year,
        ).values(
            'customer__company_name',
        ).annotate(total=Sum('total_price')).order_by('-total')
        top_sales = list(customer_sales[:5])
        total_amount = sum(float(item['total'] or 0) for item in customer_sales)
        top_amount = sum(float(item['total'] or 0) for item in top_sales)
        pie_labels = [item['customer__company_name'] for item in top_sales]
        pie_values = [float(item['total'] or 0) for item in top_sales]
        if total_amount - top_amount > 0:
            pie_labels.append('其他')
            pie_values.append(round(total_amount - top_amount, 2))

    context = {
        'today': today,
        'permissions': permissions,
        'can_contract': can_contract,
        'can_collection': can_collection,
        'can_invoice': can_invoice,
        'can_plan': can_plan,
        'can_customer': can_customer,
        'can_service': can_service,
        'can_servicedetail': can_servicedetail,
        'can_return_product': can_return_product,
        'can_chart': can_chart,
        'customer_count': customer_count,
        'contract_count': contract_stats['total_count'] or 0,
        'contract_amount': contract_stats['total_amount'] or 0,
        'year_contract_count': year_contract_stats['total_count'] or 0,
        'year_contract_amount': year_contract_stats['total_amount'] or 0,
        'month_collection_amount': month_collection_amount,
        'month_collection_count': month_collection_count,
        'quarter_collection_amount': quarter_collection_amount,
        'quarter_collection_count': quarter_collection_count,
        'month_invoice_amount': month_invoice_amount,
        'month_invoice_count': month_invoice_count,
        'pending_plans': pending_plans,
        'recent_contracts': recent_contracts,
        'recent_collections': recent_collections,
        'recent_invoices': recent_invoices,
        'upcoming_plans': upcoming_plans,
        'recent_services': recent_services,
        'recent_servicedetails': recent_servicedetails,
        'recent_return_products': recent_return_products,
        'quick_menus': quick_menus,
        'year_chart_labels': json.dumps(year_labels, ensure_ascii=False),
        'year_chart_values': json.dumps(year_amounts),
        'pie_chart_labels': json.dumps(pie_labels, ensure_ascii=False),
        'pie_chart_values': json.dumps(pie_values),
    }
    return render(request, 'index.html', context)

def page_not_found(request, exception=None):
    return render(request, '404.html',status=404)
def page_permission_denied(request, exception=None):
    return render(request, '403.html',status=403)
def pagindexter_error(request, exception=None):
    return render(request, '500.html',status=500)
