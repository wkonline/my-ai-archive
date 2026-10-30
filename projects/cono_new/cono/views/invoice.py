from django.db.models import Q, Exists, OuterRef
from django.db.models import Sum
from django.db import transaction
import datetime
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import InvoiceModelForm,UploadFileForm
from cono.tools.invoice_import import (
    InvoiceImportError,
    get_default_invoice_man_id,
    read_invoice_file,
    validate_records,
)

def invoice_list(request):
    title = "发票登记列表"
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
        q &= (Q(customer__company_name__icontains=keyword) |
              Q(contract__contract_number__icontains=keyword) |
              Q(invoice_number__icontains=keyword))
    queryset = models.Invoice.objects.filter(q).order_by("-date")
    page_object = Pagination(request, queryset)

    today = datetime.date.today()
    year_start = datetime.date(today.year, 1, 1)
    next_year_start = datetime.date(today.year + 1, 1, 1)
    month_start = datetime.date(today.year, today.month, 1)
    next_month_start = (
        datetime.date(today.year + 1, 1, 1)
        if today.month == 12
        else datetime.date(today.year, today.month + 1, 1)
    )

    chart_months = []
    chart_amounts = []
    for month in range(1, 13):
        current_start = datetime.date(today.year, month, 1)
        current_end = (
            datetime.date(today.year + 1, 1, 1)
            if month == 12
            else datetime.date(today.year, month + 1, 1)
        )
        month_total = models.Invoice.objects.filter(
            is_delete=False,
            date__gte=current_start,
            date__lt=current_end,
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_months.append('{}月'.format(month))
        chart_amounts.append(float(month_total))

    top_customers = models.Invoice.objects.filter(
        is_delete=False,
        date__gte=year_start,
        date__lt=next_year_start,
    ).values('customer__company_name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    chart_top_customers_labels = [item['customer__company_name'] for item in top_customers]
    chart_top_customers_values = [float(item['total'] or 0) for item in top_customers]

    month_customers = models.Invoice.objects.filter(
        is_delete=False,
        date__gte=month_start,
        date__lt=next_month_start,
    ).values('customer__company_name').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    chart_month_customers_labels = [item['customer__company_name'] for item in month_customers]
    chart_month_customers_values = [float(item['total'] or 0) for item in month_customers]

    context = {
        'title': title,
        'keyword': keyword,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),  # 页码
        'chart_months': json.dumps(chart_months, ensure_ascii=False),
        'chart_amounts': json.dumps(chart_amounts),
        'chart_top_customers_labels': json.dumps(chart_top_customers_labels, ensure_ascii=False),
        'chart_top_customers_values': json.dumps(chart_top_customers_values),
        'chart_month_customers_labels': json.dumps(chart_month_customers_labels, ensure_ascii=False),
        'chart_month_customers_values': json.dumps(chart_month_customers_values),
    }
    return render(request, 'invoice/invoice_list.html', context)
def get_invoice_contracts(request):
    customer_id = request.GET.get('customer_id')
    contracts = models.Contract.objects.filter(
        Q(customer_id=customer_id) & Q(invoice_completed = False)).values(
        'id', 'contract_number')
    return JsonResponse(list(contracts), safe=False)
def invoice_add(request):
    title = "新增发票记录"
    if request.method == "GET":
        queryset = InvoiceModelForm()
        context = {
            'title': title,
            "form": queryset,
        }
        return render(request, 'invoice/invoice_add.html', context)
    queryset = InvoiceModelForm(data=request.POST)
    if queryset.is_valid():
        instance = queryset.save(commit=False)
        instance.customer_id=request.POST.get('customer')
        instance.contract_id=request.POST.get('contract')
        user_id = models.User.objects.filter(username=request.info_dict_username).first().id
        instance.invoice_man_id=user_id
        instance.save()
        return redirect('/invoice/list/')
    return render(request, 'invoice/invoice_create.html', {"queryset": queryset})
def invoice_edit(request, nid):
    row_object = models.Invoice.objects.filter(id=nid).first()

    if request.method == "GET":
        form = InvoiceModelForm(instance=row_object)
        return render(request, 'invoice/invoice_edit.html', {"form": form})

    form = InvoiceModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/invoice/list/')
    return render(request, 'invoice/invoice_edit.html', {"form": form})
def invoice_delete(request):
    nid=request.GET.get('nid')
    row_object=models.Invoice.objects.get(id=nid)
    row_object.is_delete = True
    row_object.save()
    #更新合同表
    models.Contract.objects.filter(contract_number=row_object.contract).update(invoice_completed=False)
    return JsonResponse({'status': True})
def invoice_create(request):
    title = "新增发票记录"
    if request.method == "GET":
        form = InvoiceModelForm
        customers = models.Customer.objects.filter(
            Exists(models.Contract.objects.filter(
                customer=OuterRef("pk"), invoice_completed=False)))
        context = {
            'title': title,
            'customers': customers,
            'form': form,
        }
        return render(request, 'invoice/invoice_create.html', context)
    form = InvoiceModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.customer_id = request.POST.get('customer')
        instance.contract_id = request.POST.get('contract')
        instance.invoice_man_id = request.info_dict_useid
        instance.save()
        return redirect('/invoice/list/')
    return render(request, 'invoice/invoice_create.html', {"form": form})
# 批量导入发票
def invoice_multi(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        title = "文件上传成功，数据已保存到数据库！"
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                records = read_invoice_file(uploaded_file)
                prepared = validate_records(records)
            except InvoiceImportError as exc:
                return render(request, 'error.html', {'title': exc.message})

            invoice_man_id = get_default_invoice_man_id(request.info_dict_useid)
            with transaction.atomic():
                for item in prepared:
                    invoice_form = InvoiceModelForm(item['data'])
                    instance = invoice_form.save(commit=False)
                    instance.customer_id = item['customer_id']
                    instance.contract_id = item['contract_id']
                    instance.invoice_man_id = invoice_man_id
                    instance.save()
            return render(request, 'success.html', {'title': title, 'url_path': '/invoice/list/'})
    return redirect("/invoice/list/")