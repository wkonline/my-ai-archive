import pandas as pd
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from cono.tools.pagination import Pagination
from django.http import JsonResponse
from cono.tools.form import ServiceDetailModelForm,ReturnProductModelForm
from django.db.models import Q, Exists,OuterRef
import datetime
from io import BytesIO

def return_product_list(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    customer_name = request.GET.get('customer_name')
    service_number = request.GET.get('service_number')
    q_objects = Q()  # 初始化一个空的Q对象
    if start_date and end_date:
        q_objects &= Q(date__range=(start_date, end_date))
    if customer_name:
        q_objects &= Q(customer__company_name__icontains=customer_name.strip())  # 使用|表示OR逻辑
    if service_number:
        q_objects &= Q(service__service_number__icontains = service_number.strip())
    queryset = models.ReturnProduct.objects.filter(q_objects, is_delete=False).order_by("-date")
    page_object = Pagination(request, queryset)
    title = "售后返件列表"
    context = {
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'title': title,
    }
    return render(request, 'return_product/return_product_list.html', context)

def get_return_product_services(request):
    if request.method == "GET":
        customer_id = request.GET.get('customer_id')
        servers = models.Service.objects.filter(
            Q(customer_id=customer_id) & Q(warranty_end=2) & Q(return_status=1)
        ).values(
            'id',
            'service_number',
            'productcategory__name',
            'product__model',
        )
        return JsonResponse(list(servers), safe=False)
def get_return_product_model(request):
    if request.method == "GET":
        service_number = request.GET.get('service_number')
        products = models.Service.objects.filter(Q(pk=service_number) & Q(warranty_end=2)).values('productcategory__name', 'product__model')
        return JsonResponse(list(products), safe=False)
def return_product_add(request):
    if request.method == "GET":
        form = ReturnProductModelForm(initial={'date': datetime.date.today()})
        customers = models.Customer.objects.filter(
            Exists(models.Service.objects.filter(
                customer=OuterRef("pk"), warranty_end=2,return_status=1)))
        title = "新增维修记录"
        context = {
            'form': form,
            'customers': customers,
            'title': title,
        }
        return render(request, 'return_product/return_product_add.html', context)
    form = ReturnProductModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer_id = request.POST.get('customer')
        instance.service_id = request.POST.get('service')
        instance.product_id = request.POST.get('product')
        instance.productcategory_id = request.POST.get('productcategory')
        instance.user_id=request.info_dict_useid
        instance.save()
        models.Service.objects.filter(pk=instance.service_id).update(return_status=2)
        return redirect('/return_product/list/')
    return render(request, 'return_product/return_product_add.html', {"form": form})

def return_product_batch_add(request):
    title = "批量登记维修返件"
    customers = models.Customer.objects.filter(
        Exists(models.Service.objects.filter(
            customer=OuterRef("pk"), warranty_end=2, return_status=1)))
    if request.method == "GET":
        return render(request, 'return_product/return_product_batch_add.html', {
            'title': title,
            'customers': customers,
            'date': datetime.date.today(),
        })
    customer_id = request.POST.get('customer')
    customer = models.Customer.objects.filter(pk=customer_id).first()
    service_ids = request.POST.getlist('service_id')
    return_date = request.POST.get('date')
    error = ''

    if customer is None:
        error = '请选择客户名称'
    elif not any(service_ids):
        error = '该项目暂无可返件产品'
    elif not return_date:
        error = '请选择返件日期'

    if not error:
        created = 0
        for service_id in service_ids:
            if not service_id:
                continue
            service = models.Service.objects.filter(id=service_id).first()
            if service is None:
                continue
            models.ReturnProduct.objects.create(
                customer=customer,
                service=service,
                date=return_date,
                user_id=request.info_dict_useid,
            )
            service.return_status = 2
            service.save(update_fields=['return_status'])
            created += 1
        if created:
            return redirect('/return_product/list/')
        error = '未成功创建返件记录'

    return render(request, 'return_product/return_product_batch_add.html', {
        'title': title,
        'customers': customers,
        'date': return_date,
        'error': error,
        'form_data': request.POST,
    })
def return_product_delete(request):
    """ 删除售后返件 """
    nid = request.GET.get('nid')
    return_product = models.ReturnProduct.objects.filter(id=nid).first()
    if return_product:
        service_id = return_product.service_id
        models.ReturnProduct.objects.filter(id=nid).update(is_delete=True)
        # 若该维修单已无未删除的返件记录，则恢复返件状态为未发货
        if not models.ReturnProduct.objects.filter(service_id=service_id, is_delete=False).exists():
            models.Service.objects.filter(pk=service_id).update(return_status=1)
    return JsonResponse({'status': True})

def return_product_edit(request, nid):
    row_object = models.ReturnProduct.objects.filter(pk=nid).first()
    if request.method == "GET":
        form = ReturnProductModelForm(instance=row_object)
        return render(request, 'return_product/return_product_edit.html', {"form": form,'row_object':row_object})
    form = ReturnProductModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/return_product/list/')
    return render(request, 'return_product/return_product_edit.html', {"form": form})

def return_product_download_excel(request):
    return_products = models.ReturnProduct.objects.filter(is_delete=False)
    data = [{
        '客户名称': return_product.customer,
        '服务编号': return_product.service,
        '维修人': return_product.repairman,
        '故障现象': return_product.fault_text,
        '故障原因': return_product.fault_reason,
        '维修方法': return_product.repair_method,
        '维修完成时间': return_product.repair_date,
    } for return_product in return_products]
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
    filename = f"return_product_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response
