from datetime import datetime

from django.db.models import Sum,Q,DecimalField,F,Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models.functions import TruncMonth,TruncYear
from cono import models


def _salesperson_list():
    saler_ids = list(
        models.Customer.objects.filter(is_delete=False)
        .values_list('saler_id', flat=True)
        .distinct()
    )
    return list(
        models.User.objects.filter(id__in=saler_ids)
        .order_by('username')
        .values_list('id', 'username')
    )


def chart_list(request):
    title = "应收账款"
    """ 开票应收页面：展示开票未付款 / 未开票未付款合同，支持按客户名称、业务员筛选。"""
    base_contracts = (
        models.Contract.objects.filter(is_delete=False)
        .select_related('customer', 'customer__saler')
        .annotate(
            invoiced_amount=Coalesce(Sum('invoice__amount'), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))),
            collected_amount=Coalesce(Sum('collection__amount'), Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))),
        )
    )

    # 客户名称模糊筛选
    customer_name = request.GET.get('customer_name', '').strip()
    if customer_name:
        base_contracts = base_contracts.filter(
            customer__company_name__icontains=customer_name
        )

    # 业务员筛选
    salespeople = _salesperson_list()
    salesperson_id = ''
    salesperson = request.GET.get('salesperson')
    if salesperson:
        try:
            salesperson_id = int(salesperson)
        except (TypeError, ValueError):
            salesperson_id = ''
        if salesperson_id:
            base_contracts = base_contracts.filter(customer__saler_id=salesperson_id)

    # 开票未付款：已开票但回款不足
    invoiced_unpaid = base_contracts.filter(
        invoiced_amount__gt=0,
        collected_amount__lt=models.F('total_price')
    ).order_by('-date', '-order_number')

    # 未开票未付款：未开票且回款不足
    uninvoiced_unpaid = base_contracts.filter(
        invoiced_amount__exact=0,
        collected_amount__lt=models.F('total_price')
    ).order_by('-date', '-order_number')

    # 各表应收合计
    total_invoiced_outstanding = invoiced_unpaid.aggregate(
        s=Sum(F('total_price') - F('collected_amount'))
    )['s'] or 0
    total_uninvoiced_outstanding = uninvoiced_unpaid.aggregate(
        s=Sum(F('total_price') - F('collected_amount'))
    )['s'] or 0

    return render(
        request,
        'chart_list.html',
        {
            'title': title,
            'invoiced_unpaid': invoiced_unpaid,
            'uninvoiced_unpaid': uninvoiced_unpaid,
            'invoiced_unpaid_count': invoiced_unpaid.count(),
            'uninvoiced_unpaid_count': uninvoiced_unpaid.count(),
            'total_invoiced_outstanding': total_invoiced_outstanding,
            'total_uninvoiced_outstanding': total_uninvoiced_outstanding,
            'salespeople': salespeople,
            'selected_salesperson': salesperson_id if salesperson_id else '',
            'selected_customer_name': customer_name,
        }
    )

def chart_bar(request):
    """ 构造柱状图的数据 """
    db_data_list = models.Contract.objects.filter(date__range= ["2022-01-01", "2022-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2022 = []
    for item in db_data_list:
        data_list_2022.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range= ["2023-01-01", "2023-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2023 = []
    for item in db_data_list:
        data_list_2023.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range=["2024-01-01", "2024-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2024 = []
    for item in db_data_list:
        data_list_2024.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range= ["2025-01-01", "2025-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2025 = []
    for item in db_data_list:
        data_list_2025.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range=["2026-01-01", "2026-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2026 = []
    for item in db_data_list:
        data_list_2026.append(item['total_moth_price'])
    # 数据可以去数据库中获取
    legend = ["2022","2023", "2024","2025","2026"]
    series_list = [
        {
            "name": '2022',
            "type": 'bar',
            "data": data_list_2022
        },
        {
            "name": '2023',
            "type": 'bar',
            "data": data_list_2023
        },
        {
            "name": '2024',
            "type": 'bar',
            "data": data_list_2024
        },
        {
            "name": '2025',
            "type": 'bar',
            "data": data_list_2025
        },
        {
            "name": '2026',
            "type": 'bar',
            "data": data_list_2026
        },
    ]
    x_axis = ['1月', '2月', '3月','4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

    result = {
        "status": True,
        "data": {
            'legend': legend,
            'series_list': series_list,
            'x_axis': x_axis,
        }
    }
    return JsonResponse(result)

def chart_bar2(request):
    """ 构造柱状图的数据 """
    data_list = []
    db_data_list = models.Contract.objects.filter(date__range=["2013-01-01", "2026-12-31"]).annotate(
        year=TruncYear('date')).values('year').annotate(
        total_year_price=Sum('total_price')).order_by('year')
    for item in db_data_list:
        data_list.append(item['total_year_price'])
    legend = ["历年业绩图"]
    series_list = [
        {
            "name": '历年业绩图',
            "type": 'bar',
            "data": data_list
        }
    ]
    x_axis = ['2013','2014', '2015','2016','2017','2018','2019', '2020', '2021', '2022', '2023', '2024','2025','2026']

    result = {
        "status": True,
        "data": {
            'legend': legend,
            'series_list': series_list,
            'x_axis': x_axis,
        }
    }
    return JsonResponse(result)


def chart_pie(request):
    #         'customer__contract__total_price',
    # #     {"value": 580, "name": '新媒体'},
    #
    # result = {
    #     "status": True,
    #     "data": db_data_list
    # }
    # return JsonResponse(result)
    """ 构造饼图的数据 """
    saler_names = ['王传智', '郑朋辉', '董晓波','冯志宇']
    start_of_2026 = datetime(2026, 1, 1)
    end_of_2026 = datetime(2026, 12, 31)
    sales_saler_list = models.User.objects.filter(username__in=saler_names).annotate(
        total_sales_2026=Sum(
            'customer__contract__total_price',
            filter= Q(customer__contract__date__gte=start_of_2026, customer__contract__date__lte=end_of_2026)
        )
    ).order_by('username')
    db_data_list = [
        {"value": sales_saler.total_sales_2026, "name": sales_saler.username} for sales_saler in sales_saler_list
    ]
    # for sales_saler in sales_saler_list:
    #
    #     {"value": 2048, "name": 'IT部门'},
    #     {"value": 1735, "name": '运营'},
    #     {"value": 580, "name": '新媒体'},

    result = {
        "status": True,
        "data": db_data_list
    }
    return JsonResponse(result)


def chart_line(request):
    db_data_list = models.Contract.objects.filter(date__range= ["2021-01-01", "2021-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2021 = []
    for item in db_data_list:
        data_list_2021.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range= ["2022-01-01", "2022-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2022 = []
    for item in db_data_list:
        data_list_2022.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range= ["2023-01-01", "2023-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2023 = []
    for item in db_data_list:
        data_list_2023.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range=["2024-01-01", "2024-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2024 = []
    for item in db_data_list:
        data_list_2024.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range=["2025-01-01", "2025-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2025 = []
    for item in db_data_list:
        data_list_2025.append(item['total_moth_price'])
    db_data_list = models.Contract.objects.filter(date__range=["2026-01-01", "2026-12-31"]).annotate(
        month=TruncMonth('date')).values('month').annotate(
        total_moth_price=Sum('total_price')).order_by('month')
    data_list_2026 = []
    for item in db_data_list:
        data_list_2026.append(item['total_moth_price'])
    legend = ["2021","2022","2023", "2024","2025","2026"]
    series_list = [
        {
            "name": '2021',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2021
        },
        {
            "name": '2022',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2022
        },
        {
            "name": '2023',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2023
        },
        {
            "name": '2024',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2024
        },
        {
            "name": '2025',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2025
        },
        {
            "name": '2026',
            "type": 'line',
            "stack": 'Total',
            "data": data_list_2026
        }
    ]
    x_axis = ['1月', '2月', '3月','4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

    result = {
        "status": True,
        "data": {
            'legend': legend,
            'series_list': series_list,
            'x_axis': x_axis,
        }
    }
    return JsonResponse(result)


def highcharts(request):
    """ highcharts示例 """

    return render(request, 'highcharts.html')


# from django.forms import ModelForm, Form
#
# # class TTModelForm(Form):
# #     name = forms.CharField(label="用户名")
# #     ff = forms.FileField(label="文件")
# #
# #
# # def tt(request):
# #     if request.method == "GET":
# #         form = TTModelForm()
# #         return render(request, 'change.html', {"form": form})
# #     form = TTModelForm(data=request.POST, files=request.FILES)
# #     if form.is_valid():
# #         print(form.cleaned_data)
# #     return render(request, 'change.html', {"form": form})
#
# class TTModelForm(ModelForm):
#     class Meta:
#         model = models.XX
#         fields = "__all__"
#
#
# def tt(request):
#     instance = models.XX.objects.all().first()
#     if request.method == "GET":
#         form = TTModelForm(instance=instance)
#         return render(request, 'tt.html', {"form": form})
#     form = TTModelForm(data=request.POST, files=request.FILES)
#     if form.is_valid():
#         form.save()
#     return render(request, 'tt.html', {"form": form})
