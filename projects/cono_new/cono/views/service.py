import pandas as pd
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from django.http import JsonResponse
from cono.tools.pagination import Pagination
from cono.tools.form import ServiceModelForm,UploadFileForm
from django.db.models import Q, Count
import datetime
import json
from io import BytesIO

def service_list(request):
    """售后服务列表"""
    form = UploadFileForm()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    customer_name = request.GET.get('customer_name')
    keyword = request.GET.get('keyword')
    q_objects = Q()  # 初始化一个空的Q对象
    if start_date and end_date:
        q_objects &= Q(date__range=(start_date, end_date))
    if customer_name:
        q_objects &= Q(customer__company_name__icontains=customer_name.strip())  # 使用|表示OR逻辑
    if keyword:
        q_objects &= (Q(product__model__icontains=keyword.strip()) | Q(productcategory__name__icontains=keyword.strip()))
    queryset = models.Service.objects.filter(q_objects, is_delete=False).order_by("-id")
    page_object = Pagination(request, queryset)
    title = "售后列表"

    today = datetime.date.today()
    chart_months = []
    chart_month_values = []
    for month in range(1, 13):
        month_start = datetime.date(today.year, month, 1)
        month_end = (
            datetime.date(today.year + 1, 1, 1)
            if month == 12
            else datetime.date(today.year, month + 1, 1)
        )
        count = models.Service.objects.filter(
            is_delete=False,
            date__gte=month_start,
            date__lt=month_end,
        ).count()
        chart_months.append('{}月'.format(month))
        chart_month_values.append(count)

    chart_three_years = []
    for year in (today.year - 2, today.year - 1, today.year):
        values = []
        for month in range(1, 13):
            month_start = datetime.date(year, month, 1)
            month_end = (
                datetime.date(year + 1, 1, 1)
                if month == 12
                else datetime.date(year, month + 1, 1)
            )
            values.append(models.Service.objects.filter(
                is_delete=False,
                date__gte=month_start,
                date__lt=month_end,
            ).count())
        chart_three_years.append({'year': year, 'values': values})

    year_start = datetime.date(today.year, 1, 1)
    next_year_start = datetime.date(today.year + 1, 1, 1)
    customer_counts = models.Service.objects.filter(
        is_delete=False,
        date__gte=year_start,
        date__lt=next_year_start,
    ).values('customer__company_name').annotate(
        cnt=Count('id')
    ).order_by('-cnt')
    top_customers = list(customer_counts[:5])
    total_count = sum(item['cnt'] for item in customer_counts)
    top_count = sum(item['cnt'] for item in top_customers)
    chart_customer_labels = [item['customer__company_name'] for item in top_customers]
    chart_customer_values = [item['cnt'] for item in top_customers]
    if total_count - top_count > 0:
        chart_customer_labels.append('其他')
        chart_customer_values.append(total_count - top_count)

    context = {
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html() , # 页码
        'title': title,
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_month_values': json.dumps(chart_month_values),
        'chart_three_years': json.dumps(chart_three_years, ensure_ascii=False),
        'chart_customer_labels': json.dumps(chart_customer_labels, ensure_ascii=False),
        'chart_customer_values': json.dumps(chart_customer_values),
    }
    return render(request, 'service/service_list.html', context)

def _next_service_number():

    last = models.Service.objects.order_by('-id').first()
    next_id = (last.id if last else 0) + 1
    return "CN2025WX{:03d}".format(next_id)

def service_add(request):
    title = "新增售后"
    if request.method == "GET":
        form = ServiceModelForm(initial={'date': datetime.date.today()})
        service_number = _next_service_number()
        context = {
            'title': title,
            'form': form,
            'service_number': service_number,
        }
        return render(request, 'service/service_add.html', context)
    form = ServiceModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.service_number=request.POST.get('service_number')
        instance.repairman_id=request.info_dict_useid
        instance.save()
        return redirect("/service/list/")
    return render(request, 'service/service_add.html', {
        "form": form,
        "title": title,
        "service_number": request.POST.get('service_number', _next_service_number()),
    })

def service_copy(request, nid):
    """从售后列表复制一行，直接进入新增登记。"""
    row = models.Service.objects.filter(id=nid).first()
    if row is None:
        return redirect('/service/list/')
    form = ServiceModelForm(initial={
        'customer': row.customer,
        'date': datetime.date.today(),
        'productcategory': row.productcategory,
        'product': row.product,
        'product_number': row.product_number,
        'warranty': row.warranty,
        'description': row.description,
    })
    return render(request, 'service/service_add.html', {
        'title': '复制新增售后',
        'form': form,
        'service_number': _next_service_number(),
        'copy_customer_name': row.customer.company_name,
    })
def service_delete(request):
    """ 删除售后服务 """
    nid = request.GET.get('nid')
    models.Service.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})

def service_edit(request, nid):
    row_object = models.Service.objects.filter(id=nid).first()

    if request.method == "GET":
        form = ServiceModelForm(instance=row_object)
        return render(request, 'service/service_edit.html', {"form": form})

    form = ServiceModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/service/list/')

    return render(request, 'service/service_edit.html', {"form": form})

def service_download_excel(request):
    services = models.Service.objects.filter(is_delete=False)
    data = [{
        '接收日期':service.date,
        '客户名称': service.customer,
        '产品名称': service.productcategory,
        '产品型号': service.product,
        '产品编号': service.product_number,
        '维修编号': service.service_number,
        '责任人': service.repairman,
    } for service in services]
    # 将数据转换为DataFrame
    df = pd.DataFrame(data)
    output = BytesIO()
    # 使用Pandas的to_excel方法将数据写入BytesIO对象
    # 这里使用了openpyxl作为Excel文件的写入引擎
    df.to_excel(output, index=False, engine='openpyxl')
    # 将BytesIO对象的指针回到起始位置
    output.seek(0)
    # 设置HTTP响应的内容类型为Excel文件
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    datetime_now = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"service_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response

def service_detail(request, service_number):
    """维修编号详情页：显示售后服务情况、维修记录、售后返件"""
    from django.shortcuts import get_object_or_404

    # 获取售后服务记录
    service = get_object_or_404(models.Service, service_number=service_number)

    # 获取维修记录
    service_details = models.ServiceDetail.objects.filter(
        service=service
    ).select_related('customer', 'productcategory', 'product', 'repairman').order_by('-repair_date')

    # 获取售后返件
    return_products = models.ReturnProduct.objects.filter(
        service=service
    ).select_related('customer', 'user').order_by('-date')

    title = f"维修编号详情 - {service_number}"
    context = {
        'service': service,
        'service_details': service_details,
        'return_products': return_products,
        'title': title,
    }
    return render(request, 'service/service_detail.html', context)