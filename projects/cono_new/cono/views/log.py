from django.shortcuts import render, redirect, HttpResponse
from cono import models
from cono.tools.pagination import Pagination


def log_list(request):
    queryset = models.UserLog.objects.all().order_by('-id')
    page_object = Pagination(request, queryset)
    title = '操作日志列表'
    context = {
        "queryset": page_object.page_queryset,  # 分完页的数据
        "page_string": page_object.html() , # 页码
        'title': title,
    }
    return render(request, 'log/log_list.html', context)


