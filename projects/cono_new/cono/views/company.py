from django.shortcuts import render, redirect
from cono import models
from cono.tools.form import MyCompanyModelForm


def company_show(request):
    queryset = models.MyCompany.objects.all()
    title = '公司信息'
    return render(request, 'company/company_show.html', {'queryset': queryset, 'title': title})


def company_edit(request, nid):
    """ 修改公司信息 """
    row_object = models.MyCompany.objects.filter(id=nid).first()
    if row_object is None:
        return redirect('/company/list/')

    title = "修改公司信息"
    if request.method == "GET":
        form = MyCompanyModelForm(instance=row_object)
        return render(request, 'company/company_edit.html', {"form": form, "title": title})

    form = MyCompanyModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/company/list/')

    return render(request, 'company/company_edit.html', {"form": form, "title": title})
