from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import CustomerModelForm

def customer_list(request):
    """ 客户列表 """
    search_data = request.GET.get('q')
    q_objects = Q()  # 初始化一个空的Q对象
    if search_data:
        q_objects |= Q(company_name__icontains=search_data.strip())
    if search_data:
        q_objects |= Q(contact_person__icontains=search_data.strip())

    queryset = models.Customer.objects.filter(q_objects).order_by("-id")

    page_object = Pagination(request, queryset)
    title = "客户列表"
    context = {
        "title": title,
        "search_data": search_data,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html()  # 页码
    }
    return render(request, 'customer/customer_list.html', context)

def customer_add(request):
    """ 客户添加 """
    if request.method == "GET":
        form = CustomerModelForm()
        title ="新增客户"
        id_time = "id_customer_time"
        context = {
            "form": form,
            "title": title,
            "id_time":id_time
        }
        return render(request, 'change.html', context)
    form = CustomerModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/customer/list/')
    return render(request, 'change.html', {"form": form})

def customer_edit(request, nid):
    row_object = models.Customer.objects.filter(id=nid).first()

    if request.method == "GET":
        form = CustomerModelForm(instance=row_object)
        return render(request, 'customer/customer_edit.html', {"form": form})

    form = CustomerModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/customer/list/')

    return render(request, 'customer/customer_edit.html', {"form": form})

def customer_delete(request):
    nid=request.GET.get('nid')
    row_object=models.Customer.objects.get(id=nid)
    row_object.is_delete = True
    row_object.save()
    return JsonResponse({'status': True})