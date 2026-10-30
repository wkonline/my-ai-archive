from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponse
from cono import models
from cono.tools.form import WarehouseModelForm



def warehouse_list(request):
    title = "仓库列表"
    queryset = models.Warehouse.objects.all()
    return render(request, 'warehouse/warehouse_list.html', {'queryset': queryset, 'title': title})


def warehouse_add(request):
    if request.method == "GET":
        form = WarehouseModelForm()
        return render(request, 'change.html', {"form": form})
    form = WarehouseModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/warehouse/list/')
    return render(request, 'change.html', {"form": form})


def warehouse_delete(request):
    nid = request.GET.get('nid')
    models.Warehouse.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})


def warehouse_edit(request, nid):
    """ 修改仓库 """
    row_object = models.Warehouse.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/warehouse/list/')

    title = "修改仓库"
    if request.method == "GET":
        form = WarehouseModelForm(instance=row_object)
        return render(request, 'warehouse/warehouse_edit.html', {"form": form, "title": title})

    form = WarehouseModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/warehouse/list/')

    return render(request, 'warehouse/warehouse_edit.html', {"form": form, "title": title})