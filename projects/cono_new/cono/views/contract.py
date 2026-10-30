import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from io import BytesIO
from django.db import transaction
from decimal import Decimal, InvalidOperation
from cono import models
from cono.tools.pagination import Pagination
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum,Q,Max
from cono.tools.form import ContractModelForm,Product_FormSet,Product_FormSet_update,UploadFileForm,ContractProductModelForm
import datetime
import json
from django.db.models import Count

def contract_list(request):
    """合同列表"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    keyword = request.GET.get('keyword')  # 合并搜索：客户名称或合同号
    payment_completed = request.GET.get('payment_completed')
    invoice_completed = request.GET.get('invoice_completed')
    time_range = request.GET.get('time_range')  # 快捷时间筛选

    # 处理快捷时间筛选
    today = datetime.date.today()
    if time_range == 'week':
        start_date = today - datetime.timedelta(days=7)
        end_date = today
    elif time_range == 'month':
        start_date = today - datetime.timedelta(days=30)
        end_date = today
    elif time_range == 'quarter':
        start_date = today - datetime.timedelta(days=90)
        end_date = today

    q_objects = Q()
    if start_date and end_date:
        q_objects &= Q(date__range=(start_date, end_date))
    if keyword:
        # 模糊搜索：客户名称 OR 合同号，去除空格
        keyword_clean = keyword.strip().replace(' ', '')
        if keyword_clean:
            q_objects &= (Q(customer__company_name__icontains=keyword_clean) |
                          Q(contract_number__icontains=keyword_clean))
    if payment_completed:
        q_objects &= Q(payment_completed=(payment_completed == "True"))
    if invoice_completed:
        q_objects &= Q(invoice_completed=(invoice_completed == "True"))
    contracts = models.Contract.objects.filter(q_objects, is_delete=False).order_by('-order_number')
    total_amount=contracts.aggregate(contracts_amount=Sum('total_price'))
    total_count = contracts.count()
    page_object = Pagination(request, contracts)
    title = "合同列表"

    today = datetime.date.today()
    year_start = datetime.date(today.year, 1, 1)
    next_year_start = datetime.date(today.year + 1, 1, 1)
    chart_months = []
    chart_amounts = []
    for month_num in range(1, 13):
        month_start = datetime.date(today.year, month_num, 1)
        next_month_num = month_num + 1 if month_num < 12 else 1
        next_year_num = today.year if month_num < 12 else today.year + 1
        month_end = datetime.date(next_year_num, next_month_num, 1)
        month_total = models.Contract.objects.filter(
            is_delete=False,
            date__gte=month_start,
            date__lt=month_end,
        ).aggregate(total=Sum('total_price'))['total'] or 0
        chart_months.append('{}月'.format(month_num))
        chart_amounts.append(float(month_total))

    top_customers = models.Contract.objects.filter(
        is_delete=False,
        date__gte=year_start,
        date__lt=next_year_start,
    ).values('customer__company_name').annotate(
        total=Sum('total_price')
    ).order_by('-total')[:5]
    chart_customer_labels = [item['customer__company_name'] for item in top_customers]
    chart_customer_values = [float(item['total'] or 0) for item in top_customers]

    salesman_sales = models.Contract.objects.filter(
        is_delete=False,
        date__gte=year_start,
        date__lt=next_year_start,
    ).values('customer__saler__username').annotate(
        total=Sum('total_price')
    ).order_by('-total')
    chart_salesman_labels = [item['customer__saler__username'] for item in salesman_sales]
    chart_salesman_values = [float(item['total'] or 0) for item in salesman_sales]
    context = {
        "total_count": total_count,
        "total_amount":total_amount,
        "contracts": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),
        'title': title,
        'start_date': start_date,
        'end_date': end_date,
        'keyword': keyword,
        'time_range': time_range,
        'payment_completed': payment_completed,
        'invoice_completed': invoice_completed,
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_customer_labels': json.dumps(chart_customer_labels, ensure_ascii=False),
        'chart_customer_values': json.dumps(chart_customer_values),
        'chart_salesman_labels': json.dumps(chart_salesman_labels, ensure_ascii=False),
        'chart_salesman_values': json.dumps(chart_salesman_values),
    }
    return render(request, 'contract/contract_list.html', context)

def search_companys(request):
    query = request.GET.get('q')
    if query:
        companys = models.Customer.objects.filter(
            Q(company_name__icontains=query)
        ).values('id', 'company_name')
        return JsonResponse(list(companys), safe=False)
    return JsonResponse([])

def check_contract_number(request):
    """新增合同时实时检查合同编号是否重复。"""
    contract_number = request.GET.get('contract_number', '').strip()
    exclude_id = request.GET.get('exclude_id')
    if not contract_number:
        return JsonResponse({'exists': False, 'message': ''})
    contracts = models.Contract.objects.filter(contract_number=contract_number)
    if exclude_id:
        contracts = contracts.exclude(id=exclude_id)
    if contracts.exists():
        return JsonResponse({
            'exists': True,
            'message': '合同编号已存在，请更换后重试。',
        })
    return JsonResponse({'exists': False, 'message': '合同编号可用。'})

def contract_delete(request):
    """ 删除合同 """
    nid = request.GET.get('nid')
    models.Contract.objects.filter(id=nid).update(is_delete=True)
    return redirect("/contract/list/")
def contract_edit(request, nid):
    title = "合同编辑"
    contrxt_object = models.Contract.objects.filter(id=nid).first()
    product_object = models.Contract_Product.objects.filter(contract_id=nid)
    if contrxt_object is None:
        return redirect('/contract/list/')

    if request.method == "POST":
        contract_form = ContractModelForm(request.POST, request.FILES, instance=contrxt_object)
        product_formset = Product_FormSet_update(request.POST,queryset=product_object)
        customer_id = request.POST.get('customer')
        customer = models.Customer.objects.filter(id=customer_id).first() if customer_id else None
        if contract_form.is_valid() and product_formset.is_valid():
            with transaction.atomic():
                contract = contract_form.save()
                if customer:
                    contract.customer = customer
                    contract.save()
                products = product_formset.save(commit=False)
                for product in products:
                    if not product.pk:
                        product.contract = contract
                        product.customer_id = contract.customer_id
                    product.save()
                for product in product_formset.deleted_objects:
                    product.delete()

            quatity=models.Contract_Product.objects.filter(contract_id=nid).aggregate(Sum('quantity'))['quantity__sum']
            total_price=models.Contract_Product.objects.filter(contract_id=nid).aggregate(Sum('total_price'))['total_price__sum']
            models.Contract.objects.filter(id=nid).update(quantity=quatity,total_price=total_price)
            return redirect('/contract/list/')

        return render(request, 'contract/contract_edit.html', {
            'contract_form': contract_form,
            'product_formset': product_formset,
            'title': title,
            'error': '保存失败，请检查产品明细中的必填字段。',
        })
    else:
        contract_form = ContractModelForm(instance=contrxt_object)
        product_formset = Product_FormSet_update(queryset=product_object)
        customer_value = str(contrxt_object.customer.id) + '||' + str(contrxt_object.customer)
        attachment_url = ''
        attachment_name = ''
        if contrxt_object.attachment:
            try:
                attachment_url = contrxt_object.attachment.url
                attachment_name = contrxt_object.attachment.name
            except ValueError:
                pass
        return render(request, 'contract/contract_edit.html', {
            'contract_form': contract_form,
            'product_formset': product_formset,
            'title': title,
            'customer_value': customer_value,
            'attachment_url': attachment_url,
            'attachment_name': attachment_name,
        })

#合同创建
def contract_create(request):
    if request.method == 'POST':
        contract_form=ContractModelForm(request.POST, request.FILES)
        product_formset= Product_FormSet(request.POST,queryset=models.Contract_Product.objects.none())
        customer_id = request.POST.get('customer')
        customer = models.Customer.objects.filter(id=customer_id).first() if customer_id else None
        customer_error = ""
        product_error = ""
        if contract_form.is_valid() and product_formset.is_valid():
            products = product_formset.save(commit=False)
            if not customer:
                customer_error = "请先选择客户名称"
            elif not products:
                product_error = "请至少添加一条有效的产品明细"
            else:
                order_number = (models.Contract.objects.aggregate(
                    last_number=Max('order_number')
                )['last_number'] or 0) + 1
                contract = contract_form.save(commit=False)
                contract.customer = customer
                contract.order_number = order_number
                contract.save()
                quantity = 0
                total_price = Decimal("0.00")
                for product in products:
                    try:
                        product.total_price = (Decimal(product.quantity) * Decimal(product.price)).quantize(
                            Decimal("0.01")
                        )
                    except (TypeError, ValueError, InvalidOperation):
                        product.total_price = Decimal("0.00")
                    product.contract = contract
                    product.customer_id = contract.customer_id
                    product.save()
                    quantity += product.quantity or 0
                    total_price += product.total_price
                contract.quantity = quantity
                contract.total_price = total_price
                contract.save()
                return redirect('/contract/list/')
    else:
        contract_form = ContractModelForm()
        product_formset = Product_FormSet(queryset=models.Contract_Product.objects.none())
        customer_error = ""
        product_error = ""
    title = "新增合同"
    return render(request, 'contract/contract_create.html', {
        'contract_form': contract_form,
        'product_formset': product_formset,
        'title': title,
        'customer_error': customer_error,
        'product_error': product_error,
    })

def contract_product(request, nid):

    contract = models.Contract.objects.filter(id=nid).select_related(
        'customer', 'customer__saler'
    ).first()
    if contract is None:
        return redirect('/contract/list/')
    product_queryset = models.Contract_Product.objects.filter(contract_id=nid)
    invoice_queryset = models.Invoice.objects.filter(contract_id=nid).order_by('-date')
    collection_queryset = models.Collection.objects.filter(contract_id=nid).order_by('-date')
    # 查找关联的生产计划（用于查询发货信息）
    plan_queryset = models.Plan.objects.filter(contract_id=nid)
    # 通过 Plan 的 contract 关联过滤发货记录
    delivery_queryset = models.ProductDelivery.objects.filter(
        contract__contract_id=nid
    ).select_related('contract', 'contract__contract', 'delivery_man').order_by('-date')

    # 计算发货状态
    delivery_count = delivery_queryset.count()
    has_delivery = delivery_count > 0
    total_invoice = sum(i.amount for i in invoice_queryset)
    total_collection = sum(c.amount for c in collection_queryset)
    title = f"合同详情 - {contract.contract_number}"
    return render(request, 'contract/contract_product.html', {
        'queryset': product_queryset,
        'contract': contract,
        'invoice_queryset': invoice_queryset,
        'collection_queryset': collection_queryset,
        'delivery_queryset': delivery_queryset,
        'delivery_count': delivery_count,
        'has_delivery': has_delivery,
        'total_invoice': total_invoice,
        'total_collection': total_collection,
        'title': title,
    })

def product_list(request):
    search_data = request.GET.get('keyword')
    q_objects = Q()  # 初始化一个空的Q对象
    if search_data:
        q_objects &= (Q(product__model__icontains=search_data.strip()) |
                      Q(category__name__icontains=search_data.strip())|
                      Q(contract__contract_number__icontains=search_data.strip())|
                      Q(customer__company_name__icontains=search_data.strip()))
    queryset=models.Contract_Product.objects.filter(q_objects).order_by('-id')
    # # queryset = models.Contract_Product.objects.all()
    page_object = Pagination(request, queryset)
    title = "合同产品展示"
    context = {
        "search_data":search_data,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),
        'title': title,
    }
    return render(request, 'contract/product_list.html', context)

#合同产品列表
def contract_product_download_excel(request):
    contracts = models.Contract_Product.objects.order_by('-id')
    data = [{
        '合同序号': contract.contract.order_number,
        '客户名称': contract.contract.customer,
        '产品名称': contract.category,
        '产品型号': contract.product,
        '服务类型':contract.get_contract_type_display(),
        '数量': contract.quantity,
        '单价': contract.price,
        '金额': contract.total_price,
        '已开发票': contract.contract.total_invoice(),
        '已收款': contract.contract.total_collection(),
        '日期': contract.contract.date,
        '合同号': contract.contract,
    } for contract in contracts]
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
    datetime_now = datetime.datetime.now().strftime("%Y%m%d%H%M")
    filename = f"contract_product_data_{datetime_now}.xlsx"
    # filename = f"contract_data_2024.xlsx"
    # 提示下载文件而不是在浏览器中打开
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # 返回响应对象给客户端
    return response

#合同列表
def contract_download_excel(request):
    contracts = models.Contract.objects.filter(is_delete=False).order_by('-date')
    data = [{
        '序号': contract.order_number,
        '日期':contract.date,
        '客户名称': contract.customer,
        '合同号': contract.contract_number,
        '数量': contract.quantity,
        '金额': contract.total_price,
        '回款金额': contract.total_collection(),
        '已开发票': contract.total_invoice(),
        '开发票比例': "{:.2f}%".format(contract.invoice_ratio()),
        '回款比例': "{:.2f}%".format(contract.collection_ratio()),
        '业务经理': contract.customer.saler,
    } for contract in contracts]
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    datetime_now = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"contract_data_{datetime_now}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def contract_product_multi(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        title = "文件上传成功，数据已保存到数据库！"
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file)
            company_dict = {s.company_name: s for s in models.Customer.objects.all()}
            contract_dict = {s.contract_number: s for s in models.Contract.objects.all()}
            productcategory_dict = {s.name: s for s in models.ProductCategory.objects.all()}
            product_dict = {s.model: s for s in models.Product.objects.all()}
            for index, row in df.iterrows():
                customer = row['购货单位'],
                customer = customer[0]
                contract = row['合同编号'],
                contract = contract[0]
                productcategory=row['产品名称'],
                productcategory = productcategory[0]
                product=row['规格型号'],
                product = product[0]
                data = {
                    'category': productcategory_dict[productcategory],
                    'product': product_dict[product],
                    'quantity': row['数量'],
                    'price': row['单价'],
                    'total_price': row['金额'],
                    'contract_type': "sale",

                }
                # 验证发票编号是否重复
                #         Q(invoice_number=row['发票号码']) & Q(contract=contract_dict[contract])).exists():
                #     title = "发票号：%s重复登记" % row['发票号码']
                #     return render(request, 'error.html', {'title': title})
                # else:
                form = ContractProductModelForm(data)
                if form.is_valid():
                    form.instance.contract = contract_dict[contract]
                    form.save()
            return render(request, 'success.html', {'title': title, 'url_path': '/contract/product_list/'})
    return redirect('/contract/product_list/')