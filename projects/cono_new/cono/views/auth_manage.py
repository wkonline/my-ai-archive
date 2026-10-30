from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from cono import models
from cono.tools.auth_profile import (
    ensure_default_roles,
    all_permission_codes,
    permission_label,
    canonical_menus,
    grouped_permission_items,
    grouped_menus,
)

def require_admin(request):

    return request.info_dict_role != 'admin'

def role_list(request):
    if require_admin(request):
        return HttpResponse("无权访问")
    ensure_default_roles()
    roles = models.AuthRole.objects.all()
    return render(request, 'auth/role_list.html', {'roles': roles})

def role_add(request):
    if require_admin(request):
        return HttpResponse("无权访问")
    ensure_default_roles()
    if request.method == 'POST':
        key = request.POST.get('key', '').strip()
        name = request.POST.get('name', '').strip()
        permissions = request.POST.getlist('permissions')
        menu_titles = request.POST.getlist('menus')
        if not key or not name:
            return render(request, 'auth/role_edit.html', {
                'error': '角色标识和名称不能为空',
                'permission_groups': grouped_permission_items(),
                'menu_groups': grouped_menus(),
            })
        if models.AuthRole.objects.filter(key=key).exists():
            return render(request, 'auth/role_edit.html', {
                'error': '该角色标识已存在',
                'permission_groups': grouped_permission_items(),
                'menu_groups': grouped_menus(),
                'form': request.POST,
            })
        menu_map = {item['title']: item for item in canonical_menus()}
        models.AuthRole.objects.create(
            key=key,
            name=name,
            permissions=sorted(set(permissions)),
            menus=[menu_map[title] for title in menu_titles if title in menu_map],
        )
        return redirect('/auth/role/list/')
    return render(request, 'auth/role_edit.html', {
        'permission_groups': grouped_permission_items(),
        'menu_groups': grouped_menus(),
        'is_add': True,
    })

def role_edit(request, pk):
    if require_admin(request):
        return HttpResponse("无权访问")
    role = get_object_or_404(models.AuthRole, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        permissions = request.POST.getlist('permissions')
        menu_titles = request.POST.getlist('menus')
        if not name:
            return render(request, 'auth/role_edit.html', {
                'role': role,
                'error': '角色名称不能为空',
                'permission_groups': grouped_permission_items(),
                'menu_groups': grouped_menus(),
            })
        menu_map = {item['title']: item for item in canonical_menus()}
        role.name = name
        role.permissions = sorted(set(permissions))
        role.menus = [menu_map[title] for title in menu_titles if title in menu_map]
        role.save()
        return redirect('/auth/role/list/')
    return render(request, 'auth/role_edit.html', {
        'role': role,
        'permission_groups': grouped_permission_items(),
        'menu_groups': grouped_menus(),
    })

def role_delete(request, pk):
    if require_admin(request):
        return HttpResponse("无权访问")
    role = get_object_or_404(models.AuthRole, pk=pk)
    models.User.objects.filter(role=role.key).update(role='servicer')
    role.delete()
    return redirect('/auth/role/list/')

def user_permission(request, nid):
    if require_admin(request):
        return HttpResponse("无权访问")
    user = get_object_or_404(models.User, pk=nid)
    ensure_default_roles()
    profile = models.AuthUserProfile.objects.filter(user=user).first()
    if request.method == 'POST':
        role_key = request.POST.get('role')
        role = models.AuthRole.objects.filter(key=role_key).first()
        if role:
            user.role = role.key
            user.save()
        all_codes = all_permission_codes()
        extra = [code for code in all_codes if request.POST.get('allow_{}'.format(code))]
        denied = [code for code in all_codes if request.POST.get('deny_{}'.format(code))]
        menu_map = {item['title']: item for item in canonical_menus()}
        menu_titles = request.POST.getlist('menus')
        profile, _ = models.AuthUserProfile.objects.get_or_create(user=user)
        profile.extra_permissions = extra
        profile.denied_permissions = denied
        profile.menus = [menu_map[title] for title in menu_titles if title in menu_map]
        profile.menu_customize = request.POST.get('custom_menu') == '1'
        profile.save()
        return redirect('/user/list/')
    role_choices = models.AuthRole.objects.all()
    return render(request, 'auth/user_permission.html', {
        'user': user,
        'role_choices': role_choices,
        'permission_groups': grouped_permission_items(),
        'menu_groups': grouped_menus(),
        'extra_permissions': set(profile.extra_permissions) if profile else set(),
        'denied_permissions': set(profile.denied_permissions) if profile else set(),
        'user_menu_titles': {item.get('title') for item in (profile.menus if profile else [])},
        'menu_customize': profile.menu_customize if profile else False,
    })

def _permission_items():
    return [
        {'code': code, 'label': permission_label(code)}
        for code in all_permission_codes()
    ]