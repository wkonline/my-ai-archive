from django.shortcuts import render, redirect, HttpResponse
from cono import models
from django.http import JsonResponse
from cono.tools.form import ProductLabelModelForm
from cono.tools.pagination import Pagination


def productlabel_list(request):
    title = '产品铭牌'
    data_dict = {}
    search_data = request.GET.get('q', "")
    if search_data:
        data_dict["product__model__icontains"] = search_data
    queryset = models.ProductLabel.objects.filter(**data_dict).order_by("id")
    page_object = Pagination(request, queryset)
    context = {
        "title": title,
        "search_data": search_data,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html()  # 页码
    }
    return render(request, 'productlabel/productlabel_list.html',context)



def productlabel_add(request):
    if request.method == "GET":
        title = '添加铭牌'
        productes = models.Product.objects.filter(productcategory_id=10)
        form = ProductLabelModelForm()
        context = {
            'title': title,
            'form': form,
            'productes': productes
        }
        return render(request, 'productlabel/productlabel_add.html', context)
    form = ProductLabelModelForm(data=request.POST)
    if form.is_valid():
        form.instance.product_id = request.POST.get('product')
        form.save()
        return redirect('/productlabel/list/')
    return render(request, 'change.html', {"form": form})


def productlabel_delete(request):
    nid = request.GET.get('nid')
    models.ProductLabel.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})


def productlabel_edit(request, nid):
    """ 编辑铭牌 """
    title = '编辑铭牌'
    row_object = models.ProductLabel.objects.filter(id=nid).first()
    if request.method == "GET":
        form = ProductLabelModelForm(instance=row_object)
        context = {
            'title': title,
            'form': form,
        }
        return render(request, 'productlabel/productlabel_edit.html', context)

    form = ProductLabelModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/productlabel/list/')
    return render(request, 'productlabel/productlabel_edit.html', {"form": form})

