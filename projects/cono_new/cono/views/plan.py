from django.db.models import Q
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import PlanModelForm,UploadFileForm
import datetime
from datetime import  timedelta
from io import BytesIO

def plan_list(request):
    """生产计划列表"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    contract = request.GET.get('contract_number')
    completed = request.GET.get('completed')
    keyword = request.GET.get('keyword')
    q_objects = Q()  # 初始化一个空的Q对象
    if start_date and end_date:
        q_objects &= Q(effective_date__range=(start_date, end_date))
    if contract:
        q_objects &= (
            Q(contract__contract_number__icontains=contract.strip()) |
            Q(contract_reserve__icontains=contract.strip())
        )
    if completed:
        q_objects &= Q(completed=(completed == "True"))
    if keyword:
        q_objects &= (Q(product__model__icontains=keyword.strip()) | Q(productcategory__name__icontains=keyword.strip()))
    queryset = models.Plan.objects.filter(q_objects, is_delete=False).order_by("-effective_date")
    page_object = Pagination(request, queryset)
    title = "生产计划列表"
    context = {
        'title': title,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'start_date': start_date,
        'end_date': end_date,
        'contract_number': contract,
        'keyword': keyword,
        'completed': completed,
    }
    groups = {}
    for row in page_object.page_queryset:
        # 优先显示合同项目号，其次显示计划备用编号
        key = row.contract_reserve or row.contract_id
        if row.contract_reserve:
            contract_number = row.contract_reserve
            customer = '临时备用计划'
        elif row.contract and row.contract.contract_number:
            contract_number = row.contract.contract_number
            customer = row.contract.customer.company_name if row.contract.customer else ''
        else:
            contract_number = '备用编号'
            customer = '临时备用计划'
        group = groups.setdefault(key, {
            'contract': row.contract,
            'contract_number': contract_number,
            'customer': customer,
            'rows': [],
        })
        group['rows'].append(row)
    for group in groups.values():
        group['completed'] = all(row.completed for row in group['rows'])
    context['plan_groups'] = list(groups.values())
    return render(request, 'plan/plan_list.html', context)

def plan_contract_products(request):
    """按项目号读取产品明细：真实合同读合同产品，临时计划（无合同）直接读计划本身。"""
    reserve = (request.GET.get('reserve') or '').strip()
    if reserve:
        plans = models.Plan.objects.filter(
            contract_reserve=reserve,
            is_delete=False,
        ).select_related('productcategory', 'product').order_by('id')
        products = [
            {
                'category_id': plan.productcategory_id,
                'category__name': plan.productcategory.name,
                'product_id': plan.product_id,
                'product__model': plan.product.model,
                'quantity': plan.quantity,
            }
            for plan in plans
        ]
        return JsonResponse(products, safe=False)

    contract_id = request.GET.get('contract_id')
    if not contract_id:
        return JsonResponse([], safe=False)
    products = models.Contract_Product.objects.filter(
        contract_id=contract_id,
    ).select_related('category', 'product').order_by('id').values(
        'category_id',
        'category__name',
        'product_id',
        'product__model',
        'quantity',
        'contract_type',
    )
    return JsonResponse(list(products), safe=False)

def plan_add(request):
    now = datetime.datetime.now()
    one_month_ago = now - timedelta(days=160)
    categorys = models.ProductCategory.objects.all()
    valid_contract_ids = models.Contract_Product.objects.filter(
        Q(category__name__icontains='感应加热电源') | Q(category__name__icontains='感应斩波电源')
    ).values_list('contract_id', flat=True).distinct()
    contract_list = models.Contract.objects.filter(
        Q(id__in=valid_contract_ids) & Q(payment_completed=False) & Q(date__gte=one_month_ago),
    ).order_by('-date')
    unit_choices = models.Plan.UNIT_CHOICES
    placeholder_contract = models.Contract.objects.filter(
        contract_number=models.TEMP_CONTRACT_NUMBER,
    ).first()
    if placeholder_contract is None:
        first_customer = models.Customer.objects.first()
        if first_customer:
            last_order = models.Contract.objects.order_by('-order_number').values_list(
                'order_number',
                flat=True,
            ).first() or 0
            placeholder_contract = models.Contract.objects.create(
                contract_number=models.TEMP_CONTRACT_NUMBER,
                customer=first_customer,
                date=datetime.date.today(),
                quantity=0,
                total_price=0,
                order_number=last_order + 1,
            )
    title = "生产计划添加"

    if request.method == "GET":
        form_data = {'effective_date': now.strftime('%Y-%m-%d'), 'delivery_date': now.strftime('%Y-%m-%d')}
        context = {
            'title': title,
            'categorys': categorys,
            'unit_choices': unit_choices,
            'contract_list': contract_list,
            'placeholder_contract': placeholder_contract,
            'form_data': form_data,
        }
        return render(request, 'plan/plan_add.html', context)

    contract_id = request.POST.get('contract')
    contract_reserve = request.POST.get('contract_reserve', '').strip()
    error = ''
    if contract_id == 'reserve':
        contract = placeholder_contract
        if not contract:
            error = '未配置备用合同，请先在系统中添加备用合同'
        elif not contract_reserve:
            error = '请填写备用编号'
    else:
        contract = models.Contract.objects.filter(id=contract_id).first()
        contract_reserve = ''
    effective_date = request.POST.get('effective_date') or ''
    delivery_date = request.POST.get('delivery_date') or ''
    product_ids = request.POST.getlist('product')
    category_ids = request.POST.getlist('productcategory')
    quantities = request.POST.getlist('quantity')
    units = request.POST.getlist('unit')
    configurations = request.POST.getlist('configuration')
    if contract is None and not error:
        error = '请选择有效的项目号'
    elif not effective_date or not delivery_date:
        error = '请选择生产生效日期和交货日期'
    elif not any(p for p in product_ids):
        error = '该项目未获取到产品明细，请先确认合同产品信息'

    if not error:
        for index, product_id in enumerate(product_ids):
            if not product_id:
                continue
            category_id = category_ids[index] if index < len(category_ids) else ''
            try:
                quantity = int(quantities[index]) if index < len(quantities) else 0
            except (TypeError, ValueError):
                quantity = 0
            try:
                unit = int(units[index]) if index < len(units) and units[index] else 1
            except (TypeError, ValueError):
                unit = 1
            configuration = configurations[index] if index < len(configurations) else ''
            if quantity <= 0:
                error = '产品数量必须大于 0'
                break
            models.Plan.objects.create(
                contract=contract,
                contract_reserve=contract_reserve,
                productcategory_id=category_id,
                product_id=product_id,
                quantity=quantity,
                unit=unit,
                configuration=configuration,
                effective_date=effective_date,
                delivery_date=delivery_date,
                production_man_id=request.info_dict_useid,
            )
        if not error:
            return redirect('/plan/list/')

    return render(request, 'plan/plan_add.html', {
        'title': title,
        'categorys': categorys,
        'unit_choices': unit_choices,
        'contract_list': contract_list,
        'placeholder_contract': placeholder_contract,
        'error': error,
        'form_data': request.POST,
    })
    # data= {
    #     "contract_id": request.POST.get('contract'),
    #     "productcategory_id": request.POST.get('productcategory'),
    #     "product_id": request.POST.get('product'),
    #     "quantity": request.POST.get('quantity'),
    #     "configuration": request.POST.get('configuration'),
    #     "unit": request.POST.get('unit'),
    #     "effective_date": request.POST.get('effective_date'),
    #     "delivery_date": request.POST.get('delivery_date'),
    # }
    # models.Plan.objects.create(**data)
    # return redirect("/plan/list/")
def plan_delete(request):
    nid=request.GET.get('nid')
    row_object=models.Plan.objects.get(id=nid)
    row_object.is_delete = True
    row_object.save()
    return JsonResponse({'status': True})
def plan_edit(request, nid):
    title = "生产计划编辑"
    row_object = models.Plan.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/plan/list/')

    # 构造合同列表（同 plan_add）
    now = datetime.datetime.now()
    one_month_ago = now - timedelta(days=160)
    valid_contract_ids = models.Contract_Product.objects.filter(
        Q(category__name__icontains='感应加热电源') | Q(category__name__icontains='感应斩波电源')
    ).values_list('contract_id', flat=True).distinct()
    contract_list = models.Contract.objects.filter(
        Q(id__in=valid_contract_ids) & Q(payment_completed=False) & Q(date__gte=one_month_ago),
    ).order_by('-date')
    placeholder_contract = models.Contract.objects.filter(
        contract_number=models.TEMP_CONTRACT_NUMBER,
    ).first()

    if request.method == "GET":
        form = PlanModelForm(instance=row_object)
        return render(request, 'plan/plan_edit.html', {
            'title': title,
            'row_object': row_object,
            'form': form,
            'unit_choices': models.Plan.UNIT_CHOICES,
            'contract_list': contract_list,
            'placeholder_contract': placeholder_contract,
        })

    # POST: 处理合同变更
    new_contract_id = request.POST.get('contract', '').strip()
    if new_contract_id and new_contract_id != str(row_object.contract.id):
        new_contract = models.Contract.objects.filter(id=new_contract_id).first()
        if new_contract:
            row_object.contract = new_contract
            row_object.save()

    form = PlanModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/plan/list/')

    return render(request, 'plan/plan_edit.html', {
        'title': title,
        'row_object': row_object,
        'form': form,
        'unit_choices': models.Plan.UNIT_CHOICES,
        'contract_list': contract_list,
        'placeholder_contract': placeholder_contract,
    })

def plan_download_excel(request):
    items = models.Plan.objects.all()
    data = [{
        '回款日期': item.contract,
        '产品名称': item.productcategory,
        '产品型号': item.product,
        '数量': item.quantity,
        '配置': item.configuration,
        '单位': item.unit,
        '生效日期': item.effective_date,
        '交货日期': item.delivery_date,
    } for item in items]
    # data = [
    #     {'name': 'Alice', 'age': 30, 'city': 'New York'},
    #     {'name': 'Bob', 'age': 24, 'city': 'Paris'},
    #     {'name': 'Charlie', 'age': 29, 'city': 'London'},
    # ]
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
    filename = f"plan_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response

# def print_plan(request, nid):
#     pass
#     # 获取票据模板
#     html_string = render(request, 'plan/plan_print.html',{'items': items})
#     pdf = HTML(string=html_string).render()
#     return HttpResponse(pdf, content_type='application/pdf')