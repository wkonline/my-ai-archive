from django.shortcuts import render, redirect, HttpResponse
from cono import models
from django.http import JsonResponse
from cono.tools.form import DepartmentModelForm



# def department_list(request):
#     queryset = models.Department.objects.all()
#     return render(request, 'department/servicedetail_list.html', {'queryset': queryset})

def department_list(request):
    queryset = models.Department.objects.all()
    title = '部门列表'
    if request.method == 'POST':
        form = DepartmentModelForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = DepartmentModelForm()
    return render(request, 'department/department_list.html', {'queryset': queryset, 'form': form, 'title': title})



def department_add(request):
    if request.method == "GET":
        form = DepartmentModelForm()
        return render(request, 'change.html', {"form": form})
    form = DepartmentModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/department/list/')
    return render(request, 'change.html', {"form": form})


def department_delete(request):
    """ 删除部门 """
    nid = request.GET.get('nid')
    models.Department.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})


def department_edit(request, nid):
    """ 修改部门 """
    row_object = models.Department.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/department/list/')

    title = "修改部门"
    if request.method == "GET":
        form = DepartmentModelForm(instance=row_object)
        return render(request, 'department/department_edit.html', {"form": form, "title": title})

    form = DepartmentModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/department/list/')

    return render(request, 'department/department_edit.html', {"form": form, "title": title})

