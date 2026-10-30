from django.db.models import Q
from django.shortcuts import render, redirect
from cono.tools.form import ElectricalFileForm,MechanicalFileForm,BillFileForm,ContractFileForm
from cono import models
from cono.tools.pagination import Pagination


def contract_file_list(request):
    title = "项目文件管理"
    queryset =models.ContractFile.objects.filter(is_delete=False)
    page_object = Pagination(request, queryset)
    context = {
        'title': title,
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html()  # 页码
    }
    return render(request, 'upload/upload_list.html', context)

def upload_electrical_file(request):
    if request.method == 'POST':
        contract_id = request.POST.get('contract')
        obj = models.ContractFile.objects.filter(Q(contract_id=contract_id) & Q(is_delete=False)).first()
        if obj is None:
            form = ElectricalFileForm(request.POST, request.FILES)
            if form.is_valid():
                form.instance.contract_id = contract_id
                form.save()
        else :
            form = ElectricalFileForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form.save()
        return render(request, 'success.html', {'title': '文件上传成功', 'url_path': '/contract_file/list/'})
    else:
        contracts = models.Plan.objects.filter(completed_status=2)
        form = ElectricalFileForm()
    return render(request, 'upload/upload_electrical_file.html', {'form': form,'contracts': contracts})

def upload_mechanical_file(request):
    if request.method == 'POST':
        contract_id = request.POST.get('contract')
        obj = models.ContractFile.objects.filter(Q(contract_id=contract_id) & Q(is_delete=False)).first()
        if obj is None:
            form = MechanicalFileForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
        else :
            form = MechanicalFileForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form.save()
        return render(request, 'success.html', {'title': '文件上传成功', 'url_path': '/contract_file/list/'})
    else:
        form = MechanicalFileForm()
        contracts = models.Plan.objects.filter(completed_status=2)
    return render(request, 'upload/upload_electrical_file.html', {'form': form,'contracts': contracts})

def upload_bill_file(request):
    if request.method == 'POST':
        contract_id = request.POST.get('contract')
        obj = models.ContractFile.objects.filter(Q(contract_id=contract_id) & Q(is_delete=False)).first()
        if obj is None:
            form = BillFileForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
        else :
            form = BillFileForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form.save()
        return render(request, 'success.html', {'title': '文件上传成功', 'url_path': '/contract_file/list/'})
    else:
        form = BillFileForm()
        contracts = models.Plan.objects.filter(completed_status=2)
    return render(request, 'upload/upload_electrical_file.html', {'form': form,'contracts': contracts})

def edit_contract_file(request, nid):
    row_object = models.ContractFile.objects.filter(id=nid).first()

    if request.method == "GET":
        form = ContractFileForm(instance=row_object)
        return render(request, 'upload/upload_edit.html', {"form": form})

    form = ContractFileForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/contract_file/list/')

    return render(request, 'upload/upload_edit.html', {"form": form})

def delete_contract_file(request, nid):
    models.ContractFile.objects.filter(id=nid).update(is_delete = True)
    return redirect('/contract_file/list/')
