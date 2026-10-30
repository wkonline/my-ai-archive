import pandas as pd
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from cono.tools.pagination import Pagination
from django.http import JsonResponse
from cono.tools.form import TaskModelForm,TaskModelForm
from django.db.models import Q, Exists,OuterRef
import datetime
from io import BytesIO

def task_list(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    contract_number = request.GET.get('contract_number')
    keyword = request.GET.get('keyword')
    q = Q()
    if start_date and end_date:
        q &= Q(date__range=(start_date, end_date))
    if contract_number:
        q &= Q(contract__contract__contract_number__icontains=contract_number.strip())
    if keyword:
        q &= Q(productcategory__icontains=keyword.strip()) | Q(product__icontains=keyword.strip())
    queryset = models.ProductionTask.objects.filter(q).select_related(
        'contract__contract__customer', 'production_man',
    ).order_by('-date')
    page_object = Pagination(request, queryset)
    title = "生产任务单下派"
    context = {
        'title': title,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'start_date': start_date,
        'end_date': end_date,
        'contract_number': contract_number,
        'keyword': keyword,
    }
    groups = {}
    for task in page_object.page_queryset:
        plan = task.contract
        contract = plan.contract
        key = contract.id
        group = groups.setdefault(key, {
            # 无合同临时计划不显示备用合同的内部编号
            'contract_number': '' if plan.is_temp_plan else contract.contract_number,
            'is_temp': plan.is_temp_plan,
            'customer': contract.customer.company_name,
            'rows': [],
        })
        group['rows'].append(task)
    context['task_groups'] = list(groups.values())
    return render(request, 'task/task_list.html', context)

RESERVE_PREFIX = 'reserve:'

def _reserve_plans():
    """可派工的临时计划（无合同）备用编号，按生效日期倒序。"""
    rows = models.Plan.objects.filter(
        completed_status=1,
        is_delete=False,
        contract__contract_number=models.TEMP_CONTRACT_NUMBER,
    ).exclude(contract_reserve__isnull=True).exclude(
        contract_reserve='',
    ).order_by('-effective_date')
    reserves = []
    for row in rows:
        if row.contract_reserve not in reserves:
            reserves.append(row.contract_reserve)
    return reserves

def task_add(request):
    now = datetime.datetime.now()
    plan_contract_ids = models.Plan.objects.filter(
        completed_status=1,
    ).values_list('contract_id', flat=True).distinct()
    contracts = models.Contract.objects.filter(
        id__in=plan_contract_ids,
    ).exclude(contract_number=models.TEMP_CONTRACT_NUMBER).order_by('-date')
    reserve_plans = _reserve_plans()
    title = "新派任务单"
    if request.method == "GET":
        context = {
            'contracts': contracts,
            'reserve_plans': reserve_plans,
            'title': title,
            'form_data': {
                'date': now.strftime('%Y-%m-%d'),
            },
        }
        return render(request, 'task/task_add_dynamic.html', context)

    selection = (request.POST.get('contract') or '').strip()
    reserve = selection[len(RESERVE_PREFIX):].strip() if selection.startswith(RESERVE_PREFIX) else ''
    plan = None
    if reserve:
        plan = models.Plan.objects.filter(contract_reserve=reserve, is_delete=False).first()
    elif selection:
        plan = models.Plan.objects.filter(contract_id=selection).first()
    task_date = request.POST.get('date') or now.strftime('%Y-%m-%d')
    productcategories = request.POST.getlist('productcategory')
    products = request.POST.getlist('product')
    order_quantities = request.POST.getlist('order_quantity')
    error = ''
    if plan is None:
        error = '请选择有效的项目编号'
    elif not any(p for p in products):
        error = '该项目未获取到产品明细，请先确认合同产品信息'

    if not error:
        created = 0
        for index, product in enumerate(products):
            if not product:
                continue
            try:
                quantity = int(order_quantities[index]) if index < len(order_quantities) else 0
            except (TypeError, ValueError):
                quantity = 0
            if quantity <= 0:
                error = '下单数量必须大于 0'
                break
            if reserve:
                task_plan = models.Plan.objects.filter(
                    contract_reserve=reserve,
                    is_delete=False,
                    product__model=product,
                ).first() or plan
            else:
                task_plan = models.Plan.objects.filter(
                    contract_id=selection,
                    product__model=product,
                ).first() or plan
            models.ProductionTask.objects.create(
                contract=task_plan,
                date=task_date,
                productcategory=productcategories[index] if index < len(productcategories) else '',
                product=product,
                quantity=quantity,
                production_man_id=request.info_dict_useid,
            )
            created += 1
        if not error and created:
            if reserve:
                models.Plan.objects.filter(
                    contract_reserve=reserve, is_delete=False,
                ).update(completed_status=2)
            else:
                models.Plan.objects.filter(contract_id=selection).update(completed_status=2)
            return redirect('/task/list/')

    return render(request, 'task/task_add_dynamic.html', {
        'contracts': contracts,
        'reserve_plans': reserve_plans,
        'title': title,
        'error': error,
        'form_data': request.POST,
    })
def task_delete(request):

    nid = request.GET.get('nid')
    row_object = models.ProductionTask.objects.get(id=nid)
    row_object.is_delete = True
    row_object.save()
    models.Plan.objects.filter(pk=row_object.contract_id).update(completed_status=1)
    return JsonResponse({'status': True})

def task_edit(request, nid):
    row_object = models.ProductionTask.objects.filter(pk=nid).first()
    if row_object is None:
        return redirect('/task/list/')
    if request.method == "GET":
        form = TaskModelForm(instance=row_object)
        return render(request, 'task/task_edit.html', {"form": form, "row_object": row_object, "title": "生产任务单编辑"})
    form = TaskModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/task/list/')

    return render(request, 'task/task_edit.html', {"form": form, "row_object": row_object, "title": "生产任务单编辑"})

def task_download_excel(request):
    tasks = models.ProductionTask.objects.all()
    data = [{
        '客户名称': task.customer,
        '服务编号': task.service,
        '维修人': task.repairman,
        '故障现象': task.fault_text,
        '故障原因': task.fault_reason,
        '维修方法': task.repair_method,
        '维修完成时间': task.repair_date,
    } for task in tasks]
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
    filename = f"task_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response