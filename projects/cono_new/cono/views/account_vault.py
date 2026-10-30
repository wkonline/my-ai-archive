from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.auth_profile import get_session_permissions
from cono.tools.form import AccountVaultModelForm
from cono.tools.pagination import Pagination

PASSWORD_PERMISSION = 'account_vault_password'


def _can_view_password(request):
    permissions = get_session_permissions(request.info_dict_role, request.info_dict_useid)
    return PASSWORD_PERMISSION in permissions


def _category_options():
    """已有分类，用于表单提示，避免分类名称写乱导致搜不到。"""
    return list(
        models.AccountVault.objects.filter(is_delete=False)
        .exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
    )


def _fill_form(form):
    form.fields['category'].widget.attrs['list'] = 'category_options'
    return form


def account_vault_list(request):
    title = "账号密码"
    keyword = (request.GET.get('keyword') or '').strip()
    queryset = models.AccountVault.objects.filter(is_delete=False)
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) |
            Q(url__icontains=keyword) |
            Q(account__icontains=keyword) |
            Q(category__icontains=keyword) |
            Q(remark__icontains=keyword)
        )
    queryset = queryset.order_by('-id')
    page_object = Pagination(request, queryset)
    context = {
        "queryset": page_object.page_queryset,
        "page_string": page_object.html(),
        "title": title,
        "keyword": keyword,
        "total_count": queryset.count(),
        "can_view_password": _can_view_password(request),
        "category_options": _category_options(),
    }
    return render(request, 'account_vault/account_vault_list.html', context)


def account_vault_add(request):
    title = "新增平台账号"
    if request.method == "GET":
        form = _fill_form(AccountVaultModelForm())
        return render(request, 'account_vault/account_vault_form.html',
                      {"form": form, "title": title, "category_options": _category_options()})
    form = _fill_form(AccountVaultModelForm(data=request.POST))
    if form.is_valid():
        form.save()
        return redirect('/account_vault/list/')
    return render(request, 'account_vault/account_vault_form.html',
                  {"form": form, "title": title, "category_options": _category_options()})


def account_vault_edit(request, nid):
    title = "编辑平台账号"
    row_object = models.AccountVault.objects.filter(id=nid, is_delete=False).first()
    if row_object is None:
        return redirect('/account_vault/list/')

    if request.method == "GET":
        form = _fill_form(AccountVaultModelForm(instance=row_object))
        return render(request, 'account_vault/account_vault_form.html',
                      {"form": form, "title": title, "category_options": _category_options()})

    form = _fill_form(AccountVaultModelForm(data=request.POST, instance=row_object))
    if form.is_valid():
        form.save()
        return redirect('/account_vault/list/')
    return render(request, 'account_vault/account_vault_form.html',
                  {"form": form, "title": title, "category_options": _category_options()})


def account_vault_delete(request):
    nid = request.GET.get('nid')
    models.AccountVault.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})


def account_vault_password(request, nid):
    """按需返回密码明文，便于页面上查看或复制。"""
    row_object = models.AccountVault.objects.filter(id=nid, is_delete=False).first()
    if row_object is None:
        return JsonResponse({'status': False, 'error': '记录不存在'})
    return JsonResponse({'status': True, 'password': row_object.password or ''})
