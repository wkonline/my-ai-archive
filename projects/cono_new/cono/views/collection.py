import pandas as pd
from django.db.models import Q, OuterRef, Exists, Sum, Case, When, F, DecimalField, Subquery
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import CollectionModelForm
import datetime
import json
from io import BytesIO

def collection_list(request):
    title = "回款记录"
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    keyword = request.GET.get('keyword', '').strip()
    q = Q()
    if date_from and date_to:
        q &= Q(date__range=[date_from, date_to])
    elif date_from:
        q &= Q(date__gte=date_from)
    elif date_to:
        q &= Q(date__lte=date_to)
    if keyword:
        q &= Q(customer__company_name__icontains=keyword) | Q(contract__contract_number__icontains=keyword)
    queryset = models.Collection.objects.filter(q, is_delete=False).order_by("-date")
    page_object = Pagination(request, queryset)
    total_collections_amount = queryset.aggregate(collections_amount=Sum('amount'))
    total_collections_count = queryset.count()

    today = datetime.date.today()
    chart_months = []
    chart_amounts = []
    for month in range(1, 13):
        month_start = datetime.date(today.year, month, 1)
        month_end = datetime.date(today.year + 1, 1, 1) if month == 12 else datetime.date(today.year, month + 1, 1)
        month_total = models.Collection.objects.filter(
            is_delete=False,
            date__gte=month_start,
            date__lt=month_end,
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_months.append('{}月'.format(month))
        chart_amounts.append(float(month_total))

    quarter_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = datetime.date(today.year, quarter_month, 1)
    quarter_end = (
        datetime.date(today.year + 1, 1, 1)
        if quarter_month == 10
        else datetime.date(today.year, quarter_month + 3, 1)
    )
    salesman_sales = models.Collection.objects.filter(
        is_delete=False,
        date__gte=quarter_start,
        date__lt=quarter_end,
    ).values('customer__saler__username').annotate(
        total=Sum('amount')
    ).order_by('-total')
    chart_salesman_labels = [item['customer__saler__username'] for item in salesman_sales]
    chart_salesman_values = [float(item['total'] or 0) for item in salesman_sales]

    context = {
        'total_collections_count':total_collections_count,
        'total_collections_amount': total_collections_amount,
        'title': title,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_salesman_labels': json.dumps(chart_salesman_labels, ensure_ascii=False),
        'chart_salesman_values': json.dumps(chart_salesman_values),
    }
    return render(request, 'collection/collection_list.html', context)
def get_collection_contracts(request):
    if request.method == "GET":
        customer_id = request.GET.get('customer_id')
        paid_sub = models.Collection.objects.filter(
            contract=OuterRef("pk"), is_delete=False
        ).values("contract").annotate(total=Sum("amount")).values("total")[:1]
        contracts = models.Contract.objects.filter(
            customer_id=customer_id,
            is_delete=False,
        ).annotate(
            total_paid=Subquery(paid_sub),
            balance=Case(
                When(total_paid__isnull=True, then=F("total_price")),
                default=F("total_price") - F("total_paid"),
                output_field=DecimalField(),
            ),
        ).filter(balance__gt=0).values("id", "contract_number", "balance")
        return JsonResponse(list(contracts), safe=False)

def get_collection_customers(request):
    query = request.GET.get('q', '').strip()
    paid_sub = models.Collection.objects.filter(
        contract=OuterRef('pk'), is_delete=False
    ).values('contract').annotate(total=Sum('amount')).values('total')[:1]
    contracts = models.Contract.objects.filter(
        is_delete=False,
    ).annotate(
        total_paid=Subquery(paid_sub),
        balance=Case(
            When(total_paid__isnull=True, then=F('total_price')),
            default=F('total_price') - F('total_paid'),
            output_field=DecimalField(),
        ),
    ).filter(balance__gt=0)
    if query:
        contracts = contracts.filter(customer__company_name__icontains=query)
    result = list(contracts.values('customer_id', 'customer__company_name').distinct()[:20])
    return JsonResponse([{'id': r['customer_id'], 'company_name': r['customer__company_name']} for r in result], safe=False)
def collection_create(request):
    """旧的新增入口统一跳转到唯一入口。"""
    return redirect('/collection/add/')

def collection_edit(request, nid):
    row_object = models.Collection.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/collection/list/')

    title = "编辑回款记录"

    if request.method == "GET":
        form = CollectionModelForm(instance=row_object)
        return render(request, 'collection/collection_edit.html', {
            'title': title,
            'form': form,
            'collection': row_object,
        })

    form = CollectionModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/collection/list/')

    return render(request, 'collection/collection_edit.html', {
        'title': title,
        'form': form,
        'collection': row_object,
    })
def collection_delete(request):
    nid=request.GET.get('nid')
    row_object=models.Collection.objects.get(id=nid)
    row_object.is_delete = True
    row_object.save()
    # 更新合同表回款状态
    models.Contract.objects.filter(contract_number=row_object.contract).update(payment_completed=False)
    return JsonResponse({'status': True})
def _build_customer_contracts_data():
    """构建客户-合同数据，供前端本地使用"""
    from decimal import Decimal
    customers = list(models.Customer.objects.order_by('company_name'))
    if not customers:
        return []
    contract_ids = [c.id for c in customers]
    customer_map = {c.id: c.company_name for c in customers}
    # 一次查询所有合同的已回款金额
    paid_sub = models.Collection.objects.filter(
        contract=OuterRef('pk'), is_delete=False
    ).values('contract').annotate(total=Sum('amount')).values('total')[:1]
    contracts = models.Contract.objects.filter(
        customer_id__in=contract_ids, is_delete=False
    ).annotate(total_paid=Subquery(paid_sub))
    data = {}
    for ct in contracts:
        total_paid = float(ct.total_paid or Decimal('0'))
        balance = float(Decimal(ct.total_price) - Decimal(total_paid))
        if balance > 0:
            cid = str(ct.customer_id)
            if cid not in data:
                data[cid] = {'id': ct.customer_id, 'name': customer_map.get(ct.customer_id, ''), 'contracts': []}
            data[cid]['contracts'].append({
                'id': ct.id,
                'number': ct.contract_number,
                'balance': balance,
            })
    return [v for v in data.values() if v['contracts']]

def collection_add(request):
    title = "新增回款记录"
    if request.method == "GET":
        form = CollectionModelForm()
        customer_contracts_data = _build_customer_contracts_data()
        context = {
            'title': title,
            'form': form,
            'customer_contracts_data': customer_contracts_data,
        }
        return render(request, 'collection/collection_add.html', context)
    form = CollectionModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer_id = request.POST.get('customer')
        instance.contract_id = request.POST.get('contract')
        instance.save()
        return redirect('/collection/list/')
    return render(request, 'collection/collection_add.html', {'title': title, 'form': form})

def collection_download_excel(request):
    collections = models.Collection.objects.all().order_by('-date')
    data = [{
        '回款日期':collection.date,
        '客户名称': collection.customer,
        '合同号码': collection.contract,
        '合同金额': collection.contract.total_price,
        '回款金额':collection.amount,
        '回款方式':collection.get_collection_method_display(),
        '回款比例':"{:.2f}%".format(collection.contract.collection_ratio()),
        '业务经理':collection.contract.customer.saler,
    } for collection in collections]
    # 构建导出数据
    data = [{
        '回款日期':collection.date,
        '客户名称': collection.customer,
        '合同号码': collection.contract,
        '合同金额': collection.contract.total_price,
        '回款金额':collection.amount,
        '回款方式':collection.get_collection_method_display(),
        '回款比例':"{:.2f}%".format(collection.contract.collection_ratio()),
        '业务经理':collection.contract.customer.saler,
    } for collection in collections]
    # 转换为Excel
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    datetime_now = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"collection_data_{datetime_now}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response