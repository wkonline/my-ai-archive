import pandas as pd
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from cono.tools.pagination import Pagination
from django.http import JsonResponse
from cono.tools.form import ServiceDetailModelForm
from cono.tools.repair_kb import build_knowledge
from django.db.models import Q, Exists,OuterRef, Count
import datetime
import json
from io import BytesIO

def servicedetail_list(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    customer_name = request.GET.get('customer_name')
    keyword = request.GET.get('keyword')
    q_objects = Q()  # 初始化一个空的Q对象
    if start_date and end_date:
        q_objects &= Q(receive_date__range=(start_date, end_date))
    if customer_name:
        q_objects &= Q(customer__company_name__icontains=customer_name.strip())  # 使用|表示OR逻辑
    if keyword:
        q_objects &= (Q(product__model__icontains=keyword.strip())|Q(productcategory__name__icontains=keyword.strip()))
    queryset = models.ServiceDetail.objects.filter(q_objects, is_delete=False).order_by("-id")
    page_object = Pagination(request, queryset)

    # querysets =models.ServiceDetail.objects.all()
    # for queryset in querysets:
    #     service=queryset.service
    #     queryset.customer_id=customer_id
    #     queryset.save()
    title = "维修记录列表"
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
        count = models.ServiceDetail.objects.filter(
            is_delete=False,
            repair_date__gte=month_start,
            repair_date__lt=month_end,
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
            values.append(models.ServiceDetail.objects.filter(
                is_delete=False,
                repair_date__gte=month_start,
                repair_date__lt=month_end,
            ).count())
        chart_three_years.append({'year': year, 'values': values})

    month_start = datetime.date(today.year, today.month, 1)
    next_month_start = (
        datetime.date(today.year + 1, 1, 1)
        if today.month == 12
        else datetime.date(today.year, today.month + 1, 1)
    )
    repairman_counts = models.ServiceDetail.objects.filter(
        is_delete=False,
        repair_date__gte=month_start,
        repair_date__lt=next_month_start,
    ).values('repairman__username').annotate(
        cnt=Count('id')
    ).order_by('-cnt')
    chart_repairman_labels = [item['repairman__username'] for item in repairman_counts]
    chart_repairman_values = [item['cnt'] for item in repairman_counts]

    context = {
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'title': title,
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_month_values': json.dumps(chart_month_values),
        'chart_three_years': json.dumps(chart_three_years, ensure_ascii=False),
        'chart_repairman_labels': json.dumps(chart_repairman_labels, ensure_ascii=False),
        'chart_repairman_values': json.dumps(chart_repairman_values),
    }
    return render(request, 'servicedetail/servicedetail_list.html', context)

def get_servicedetail_services(request):
    if request.method == "GET":
        customer_id = request.GET.get('customer_id')
        servers = models.Service.objects.filter(
            Q(customer_id=customer_id) & Q(warranty_end=1)
        ).values(
            'id',
            'service_number',
            'productcategory_id',
            'productcategory__name',
            'product_id',
            'product__model',
        )
        return JsonResponse(list(servers), safe=False)
# def get_product_model(request):
#     if request.method == "GET":
#         service_number = request.GET.get('service_number')
#         contract_id = request.GET.get('contract')
#         if service_number:
#         return JsonResponse(list(products), safe=False)
def get_product_model(request):
    if request.method == "GET":
        service_number = request.GET.get('service_number')
        contract_id = request.GET.get('contract')
        print(contract_id)
        # 检查 service_number 是否不为空
        if service_number:
            # 如果 service_number 不为空，则根据 service_number 和 warranty_end=1 来查询 Service 模型
            products = models.Service.objects.filter(Q(pk=service_number) & Q(warranty_end=1)).values('productcategory__name', 'product__model')
        elif contract_id:
            # 如果 contract 不为空且 service_number 为空，则根据 contract 来查询 ProductionPlan 模型
            products = models.Plan.objects.filter(pk=contract_id).values(
                'productcategory__name',
                'product__model',
                'quantity',
                'contract__customer__contact_person',
                'contract__customer__phone',
                'contract__customer__address',
            )
        else:
            # 如果两者都为空，可以返回一个空列表或适当的错误响应
            products = []
            # 返回 JSON 响应
        return JsonResponse(list(products), safe=False)

def servicedetail_add(request):
    if request.method == "GET":
        form = ServiceDetailModelForm(initial={'repair_date': datetime.date.today()})
        customers = models.Customer.objects.filter(
            Exists(models.Service.objects.filter(
                customer=OuterRef("pk"), warranty_end=1)))
        title = "新增维修记录"
        context = {
            'customers': customers,
            'form': form,
            'title': title,
        }
        return render(request, 'servicedetail/servicedetail_add.html', context)
    form = ServiceDetailModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer_id = request.POST.get('customer')
        instance.service_id = request.POST.get('service_number')
        instance.product_id = models.Product.objects.get(model=request.POST.get('product')).id
        instance.productcategory_id = models.ProductCategory.objects.get(name=request.POST.get('productcategory')).id
        instance.repairman_id=request.info_dict_useid
        instance.save()
        models.Service.objects.filter(pk=instance.service_id).update(warranty_end=2)
        return redirect('/servicedetail/list/')
    return render(request, 'servicedetail/servicedetail_add.html', {"form": form})

def servicedetail_batch_add(request):
    title = "批量登记维修记录"
    customers = models.Customer.objects.filter(
        Exists(models.Service.objects.filter(
            customer=OuterRef("pk"), warranty_end=1)))
    if request.method == "GET":
        return render(request, 'servicedetail/servicedetail_batch_add.html', {
            'title': title,
            'customers': customers,
            'repair_date': datetime.date.today(),
        })

    customer_id = request.POST.get('customer')
    customer = models.Customer.objects.filter(pk=customer_id).first()
    service_ids = request.POST.getlist('service_id')
    productcategory_ids = request.POST.getlist('productcategory_id')
    product_ids = request.POST.getlist('product_id')
    fault_texts = request.POST.getlist('fault_text')
    fault_reasons = request.POST.getlist('fault_reason')
    repair_methods = request.POST.getlist('repair_method')
    repair_date = request.POST.get('repair_date')
    error = ''

    if customer is None:
        error = '请选择客户名称'
    elif not any(s for s in service_ids):
        error = '该项目暂无待维修产品'
    elif not repair_date:
        error = '请选择维修完成时间'

    if not error:
        created = 0
        for index, service_id in enumerate(service_ids):
            if not service_id:
                continue
            category_id = productcategory_ids[index] if index < len(productcategory_ids) else ''
            product_id = product_ids[index] if index < len(product_ids) else ''
            fault_text = fault_texts[index] if index < len(fault_texts) else ''
            fault_reason = fault_reasons[index] if index < len(fault_reasons) else ''
            repair_method = repair_methods[index] if index < len(repair_methods) else ''
            if not fault_text or not fault_reason or not repair_method:
                error = '故障现象、故障原因、维修方法均不能为空'
                break
            models.ServiceDetail.objects.create(
                customer=customer,
                service_id=service_id,
                productcategory_id=category_id or None,
                product_id=product_id or None,
                repairman_id=request.info_dict_useid,
                fault_text=fault_text,
                fault_reason=fault_reason,
                repair_method=repair_method,
                repair_date=repair_date,
            )
            models.Service.objects.filter(pk=service_id).update(warranty_end=2)
            created += 1
        if not error and created:
            return redirect('/servicedetail/list/')

    return render(request, 'servicedetail/servicedetail_batch_add.html', {
        'title': title,
        'customers': customers,
        'repair_date': repair_date,
        'error': error,
        'form_data': request.POST,
    })
def servicedetail_delete(request):
    nid = request.GET.get('nid')
    instance = models.ServiceDetail.objects.get(id=nid)
    instance.is_delete = True
    instance.save()
    models.Service.objects.filter(service_number=instance.service).update(warranty_end=1)
    return JsonResponse({'status': True})

def servicedetail_edit(request, nid):
    row_object = models.ServiceDetail.objects.filter(pk=nid).first()
    if request.method == "GET":
        form = ServiceDetailModelForm(instance=row_object)
        return render(request, 'servicedetail/servicedetail_edit.html', {"form": form,'row_object':row_object})
    form = ServiceDetailModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/servicedetail/list/')

    return render(request, 'servicedetail/servicedetail_edit.html', {"form": form})
def servicedetail_download_excel(request):
    servicedetails = models.ServiceDetail.objects.filter(is_delete=False)
    data = [{
        '客户名称': servicedetail.customer,
        '服务编号': servicedetail.service,
        '产品名称': servicedetail.productcategory,
        '产品型号': servicedetail.product,
        '维修人': servicedetail.repairman,
        '故障现象': servicedetail.fault_text,
        '故障原因': servicedetail.fault_reason,
        '维修方法': servicedetail.repair_method,
        '维修完成时间': servicedetail.repair_date,
    } for servicedetail in servicedetails]
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
    filename = f"servicedetail_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response

def servicedetail_knowledge(request):
    """维修知识库：按故障现象检索历史案例并归纳维修方法。"""
    query = (request.GET.get('q') or '').strip()
    knowledge = build_knowledge(query)
    return render(request, 'servicedetail/servicedetail_knowledge.html', {
        'title': '维修知识库',
        'query': query,
        'cases': knowledge['cases'],
        'summary': knowledge['summary'],
    })