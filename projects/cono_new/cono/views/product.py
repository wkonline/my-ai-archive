from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from django.http import JsonResponse
from cono.tools.form import ProductModelForm
from django.db.models import Q
from cono.tools import form
from cono.tools.pagination import Pagination


def product_list(request):
    search_data = request.GET.get('keyword')
    q_objects = Q()  # 初始化一个空的Q对象
    if search_data:
        q_objects &= (Q(model__icontains=search_data.strip())|
                      Q(productcategory__name__icontains=search_data.strip()))
    queryset=models.Product.objects.filter(q_objects).order_by('-id')
    page_object = Pagination(request, queryset)
    title = "产品型号列表"
    context = {
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html(),
        'title': title,
    }
    return render(request, 'product/product_list.html', context)
def product_add(request):
    title = "产品型号添加"
    if request.method == "GET":
        form = ProductModelForm()
        return render(request, 'product/product_add.html', {"form": form, 'title': title})
    form = ProductModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/product/list/')
    return render(request, 'product/product_add.html', {"form": form})
def search_warehouses(request):
    query = request.GET.get('q', '')
    if query:
        warehouses = models.Warehouse.objects.filter(
            Q(name__icontains=query)
        ).values('id', 'name')
        return JsonResponse(list(warehouses), safe=False)
    return JsonResponse([])
def product_delete(request):
    nid=request.GET.get('nid')
    models.Product.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})
def product_edit(request, nid):
    row_object = models.Product.objects.filter(id=nid).first()
    if request.method == "GET":
        form = ProductModelForm(instance=row_object)
        return render(request, 'product/product_edit.html', {"form": form})

    form = ProductModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/product/list/')

    return render(request, 'product/product_edit.html', {"form": form})

