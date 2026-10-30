import pandas as pd
import datetime
import json
from django.shortcuts import render, redirect, HttpResponse
from django.db.models import Q, OuterRef, Exists, Sum
from cono import models
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from cono.tools.form import DeliveryForm,UploadFileForm
from cono.tools.pagination import Pagination

def delivery_list(request):
    queryset = models.ProductDelivery.objects.filter(is_delete=False).order_by('-date')
    page_object = Pagination(request, queryset)
    title = "发货流水单"

    today = datetime.date.today()
    chart_months = []
    chart_values = []
    for month in range(1, 13):
        month_start = datetime.date(today.year, month, 1)
        month_end = datetime.date(today.year + 1, 1, 1) if month == 12 else datetime.date(today.year, month + 1, 1)
        total = models.ProductDelivery.objects.filter(
            is_delete=False,
            date__gte=month_start,
            date__lt=month_end,
        ).aggregate(total=Sum('quantity'))['total'] or 0
        chart_months.append('{}月'.format(month))
        chart_values.append(int(total))

    context = {
        'title': title,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_values': json.dumps(chart_values),
        'chart_total': sum(chart_values),
    }
    return render(request, 'delivery/delivery_list.html', context)

def delivery_add(request):
    customers = models.Customer.objects.filter(
        Exists(models.Contract.objects.filter(
            customer=OuterRef("pk"), payment_completed=False))).order_by('company_name')
    if request.method == "GET":
        contracts = models.Plan.objects.filter(completed_status=2)
        form= DeliveryForm()
        title = "新增发货单"
        context = {
            'form':form,
            'contracts': contracts,
            'customers': customers,
            'title': title,
        }
        return render(request, 'delivery/delivery_add.html', context)
    form = DeliveryForm(data=request.POST)
    plan = models.Plan.objects.filter(
        pk=request.POST.get('contract'),
    ).select_related('contract__customer').first()
    if plan is None:
        form.add_error(None, '请选择有效的项目编号')

    receiver = request.POST.get('receiver', '').strip()
    receiver_phone = request.POST.get('receiver_phone', '').strip()
    receiver_address = request.POST.get('receiver_address', '').strip()
    delivery_quantity = 0

    if plan and form.is_valid():
        try:
            delivery_quantity = int(request.POST.get('quantity') or 0)
        except (TypeError, ValueError):
            delivery_quantity = 0

        delivered_quantity = models.ProductDelivery.objects.filter(
            contract=plan,
        ).aggregate(total=Sum('quantity'))['total'] or 0
        remaining_quantity = max(plan.quantity - delivered_quantity, 0)

        if delivery_quantity <= 0:
            form.add_error(None, '发货数量必须大于 0')
        elif delivery_quantity > remaining_quantity:
            form.add_error(None, '发货数量不能大于剩余计划数量 {}'.format(remaining_quantity))

    if plan and form.is_valid():
        customer = models.Customer.objects.filter(
            pk=request.POST.get('customer'),
        ).first() or plan.contract.customer
        customer.contact_person = receiver or customer.contact_person
        customer.phone = receiver_phone or customer.phone
        customer.address = receiver_address or customer.address
        customer.save()

        instance = form.save(commit=False)
        instance.customer = customer
        instance.contract = plan
        instance.productcategory = request.POST.get('productcategory')
        instance.product = request.POST.get('product')
        instance.quantity = delivery_quantity
        instance.delivery_man_id = request.info_dict_useid
        instance.save()

        delivered_quantity = models.ProductDelivery.objects.filter(
            contract=plan,
        ).aggregate(total=Sum('quantity'))['total'] or 0
        if delivered_quantity >= plan.quantity:
            plan.completed_status = 3
            plan.completed = True
        else:
            plan.completed_status = 2
            plan.completed = False
        plan.save()
        return redirect('/delivery/list/')

    title = "新增发货单"
    contracts = models.Plan.objects.filter(completed_status=2)
    return render(request, 'delivery/delivery_add.html', {
        'form': form,
        'contracts': contracts,
        'customers': customers,
        'title': title,
    })

def customer_info(request):
    """按客户 ID 返回收货联系人、电话、地址。"""
    customer = models.Customer.objects.filter(
        pk=request.GET.get('customer'),
    ).values('contact_person', 'phone', 'address').first()
    if not customer:
        return JsonResponse({'contact_person': '', 'phone': '', 'address': ''})
    return JsonResponse(customer)

def _refresh_plan_delivery_status(plan):
    """按累计发货数量刷新生产计划的完结状态。"""
    delivered_quantity = models.ProductDelivery.objects.filter(
        contract=plan,
    ).aggregate(total=Sum('quantity'))['total'] or 0
    if delivered_quantity >= plan.quantity:
        plan.completed_status = 3
        plan.completed = True
    else:
        plan.completed_status = 2
        plan.completed = False
    plan.save()

def delivery_delete(request):
    nid = request.GET.get('nid')
    row_object = models.ProductDelivery.objects.get(id=nid)
    plan = row_object.contract
    row_object.is_delete = True
    row_object.save()
    _refresh_plan_delivery_status(plan)
    return JsonResponse({'status': True})

def delivery_edit(request, nid):
    title = "编辑发货单"
    row_object = models.ProductDelivery.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/delivery/list/')
    customers = models.Customer.objects.filter(
        Exists(models.Contract.objects.filter(
            customer=OuterRef("pk"), payment_completed=False))).order_by('company_name')
    contracts = models.Plan.objects.filter(completed_status=2)
    if request.method == "GET":
        form = DeliveryForm(instance=row_object)
        context = {
            'form': form,
            'row_object': row_object,
            'contracts': contracts,
            'customers': customers,
            'title': title,
        }
        return render(request, 'delivery/delivery_edit.html', context)

    form = DeliveryForm(data=request.POST, instance=row_object)
    receiver = request.POST.get('receiver', '').strip()
    receiver_phone = request.POST.get('receiver_phone', '').strip()
    receiver_address = request.POST.get('receiver_address', '').strip()
    delivery_quantity = 0
    try:
        delivery_quantity = int(request.POST.get('quantity') or 0)
    except (TypeError, ValueError):
        delivery_quantity = 0

    if row_object and form.is_valid():
        plan = models.Plan.objects.filter(
            pk=request.POST.get('contract'),
        ).select_related('contract__customer').first()
        if plan is None:
            form.add_error(None, '请选择有效的项目编号')
        else:
            # 已发货量 = 当前记录数量 + 其他记录数量
            other_delivered = (
                models.ProductDelivery.objects.filter(contract=plan, is_delete=False)
                .exclude(id=row_object.id).aggregate(total=Sum('quantity'))['total'] or 0
            )
            total_delivered = other_delivered + (row_object.quantity or 0)
            remaining_quantity = max(plan.quantity - total_delivered, 0)
            new_total = other_delivered + delivery_quantity
            if delivery_quantity <= 0:
                form.add_error(None, '发货数量必须大于 0')
            elif new_total > plan.quantity:
                form.add_error(None, '发货数量不能超出合同总数 {}'.format(plan.quantity))

    if row_object and form.is_valid() and not form.errors:
        customer = models.Customer.objects.filter(
            pk=request.POST.get('customer'),
        ).first() or row_object.customer
        customer.contact_person = receiver or customer.contact_person
        customer.phone = receiver_phone or customer.phone
        customer.address = receiver_address or customer.address
        customer.save()

        plan = models.Plan.objects.filter(
            pk=request.POST.get('contract'),
        ).select_related('contract__customer').first()
        instance = form.save(commit=False)
        instance.customer = customer
        instance.contract = plan
        instance.productcategory = request.POST.get('productcategory')
        instance.product = request.POST.get('product')
        instance.quantity = delivery_quantity
        instance.save()

        total_delivered = (
            models.ProductDelivery.objects.filter(contract=plan, is_delete=False)
            .exclude(id=row_object.id).aggregate(total=Sum('quantity'))['total'] or 0
        ) + delivery_quantity
        if total_delivered >= plan.quantity:
            plan.completed_status = 3
            plan.completed = True
        else:
            plan.completed_status = 2
            plan.completed = False
        plan.save()
        return redirect('/delivery/list/')

    context = {
        'form': form,
        'row_object': row_object,
        'contracts': contracts,
        'customers': customers,
        'title': title,
    }
    return render(request, 'delivery/delivery_edit.html', context)

def delivery_multi(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        title = "文件上传成功，数据已保存到数据库！"
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file)
            contract_dict = {s.contract.contract_number: s for s in models.Plan.objects.all()}
            productcategory_dict = {s.name: s for s in models.ProductCategory.objects.all()}
            product_dict = {s.model: s for s in models.Product.objects.all()}
            for index, row in df.iterrows():
                contract = row['合同编号'],
                contract = contract[0]
                productcategory=row['产品名称'],
                productcategory = productcategory[0]
                product=row['规格型号'],
                product = product[0]
                data = {
                    'date':row['交货日期'],
                }
                form = DeliveryForm(data)
                print( form.errors)
                if form.is_valid():
                    form.instance.contract = contract_dict[contract]
                    form.instance.productcategory = productcategory_dict[productcategory]
                    form.instance.product = product_dict[product]
                    form.instance.quantity = row['数量']
                    form.instance.delivery_man_id = 17
                    form.save()
            return render(request, 'success.html', {'title': title, 'url_path': '/delivery/list/'})
    return redirect("/delivery/list/")

def delivery_download_excel(request):
    deliveries = models.ProductDelivery.objects.select_related('customer', 'contract', 'delivery_man').all().order_by('-date')
    data = [{
        '客户名称': delivery.customer.company_name,
        '发货日期': delivery.date,
        '项目编号': delivery.contract.contract.contract_number if delivery.contract and delivery.contract.contract else '',
        '产品名称': delivery.productcategory,
        '产品型号': delivery.product,
        '数量': delivery.quantity,
        '收货人': delivery.customer.contact_person,
        '收货人联系电话': delivery.customer.phone,
        '收货地址等': delivery.customer.address,
        '发货人': delivery.delivery_man.username,
    } for delivery in deliveries]
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    import datetime
    filename = f"delivery_data_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
