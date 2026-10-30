from django.core.exceptions import ValidationError
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from django import forms
from cono.tools.form import ProductCategoryModelForm,UploadFileForm

def productcategory_list(request):
    title = "产品类别列表"
    queryset = models.ProductCategory.objects.all()
    form = UploadFileForm()
    context = {'queryset': queryset,'form': form,'title':title}
    return render(request, 'productcategory/productcategory_list.html', context)

def productcategory_add(request):
    """ 添加仓库 """
    if request.method == "GET":
        form = ProductCategoryModelForm()
        return render(request, 'change.html', {"form": form})
    form = ProductCategoryModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/productcategory/list/')
    return render(request, 'change.html', {"form": form})

def productcategory_delete(request):
    """ 删除产品分类 """
    nid = request.GET.get('nid')
    models.ProductCategory.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})
def productcategory_edit(request, nid):
    """ 修改产品分类 """
    row_object = models.ProductCategory.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/productcategory/list/')

    title = "修改产品分类"
    if request.method == "GET":
        form = ProductCategoryModelForm(instance=row_object)
        return render(request, 'productcategory/productcategory_edit.html', {"form": form, "title": title})

    form = ProductCategoryModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/productcategory/list/')

    return render(request, 'productcategory/productcategory_edit.html', {"form": form, "title": title})


def productcategory_multi(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        title="文件上传成功，数据已保存到数据库！"
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file)
            # 将DataFrame中的数据批量保存到数据库
            for index, row in df.iterrows():
                if models.ProductCategory.objects.filter(name=row['产品名称']).exists():
                   print("产品名称%s重复"%row['产品名称'])
                else:
                    models.ProductCategory.objects.create(name=row['产品名称'], )
            return render(request, 'success.html', {'title': title, 'url_path': '/productcategory/list/'})
    return redirect("/productcategory/list/")