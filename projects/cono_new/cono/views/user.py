from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, redirect
from cono import models
from cono.tools.pagination import Pagination
from cono.tools.form import UserModelForm, UserResetModelForm, ProfileEditModelForm, ChangePasswordForm
from cono.tools.encrypt import md5
from cono.tools.auth_profile import default_role_key

def user_list(request):
    """ 用户管理 """
    queryset = models.User.objects.all()
    page_object = Pagination(request, queryset, page_size=15)
    title = "用户管理"
    context = {
        'title': title,
        "queryset": page_object.page_queryset,
        "page_string": page_object.html(),
    }
    return render(request, 'user/user_list.html', context)

def user_add(request):
    title = "添加用户"
    if request.method == "GET":
        form = UserModelForm()
        return render(request, 'change.html', {"form": form, "title": title})

    form = UserModelForm(data=request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.create_date = date.today()
        instance.role = default_role_key()
        instance.save()
        return redirect('/user/list/')

    return render(request, 'change.html', {"form": form})

def user_edit(request, nid):
    """ 编辑用户 """
    row_object = models.User.objects.filter(id=nid).first()
    is_self = int(nid) == request.info_dict_useid

    if request.method == "GET":
        if is_self:
            title = "修改我的资料"
            form = ProfileEditModelForm(instance=row_object)
        else:
            title = "修改-{}-的个人资料".format(row_object.username)
            form = UserModelForm(instance=row_object)
        return render(request, 'change.html', {'form': form, "title": title})

    form = ProfileEditModelForm(data=request.POST, instance=row_object) if is_self else UserModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        if is_self:
            return render(request, 'user/profile_success.html', {
                'title': '个人资料修改成功',
                'continue_url': '/user/{}/edit/'.format(request.info_dict_useid),
            })
        return redirect('/user/list/')
    return render(request, 'user/user_edit.html', {"form": form})

def user_delete(request):
    nid = request.GET.get('nid')
    models.User.objects.filter(id=nid).update(is_delete=True)
    return JsonResponse({'status': True})

def user_reset(request, nid):
    """ 重置密码 """
    row_object = models.User.objects.filter(id=nid).first()
    if not row_object:
        return redirect('/user/list/')

    title = "重置密码-{}".format(row_object.username)
    is_self = int(nid) == request.info_dict_useid

    if request.method == "GET":
        form = UserResetModelForm()
        return render(request, 'change.html', {"form": form, "title": title})

    form = UserResetModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return render(request, 'user/profile_success.html', {
            'title': '密码修改成功',
            'continue_url': '/user/{}/reset/'.format(nid) if is_self else '/user/list/',
        })
    return render(request, 'change.html', {"form": form, "title": title})

def user_profile(request):
    """ 个人信息详细页 """
    user = models.User.objects.filter(id=request.info_dict_useid).first()
    if not user:
        return redirect('/login/')

    # 获取用户的操作日志（最近10条）
    user_logs = models.UserLog.objects.filter(user_id=request.info_dict_useid).order_by('-timestamp')[:10]

    # 统计信息
    stats = {
        'total_contracts': models.Contract.objects.filter(customer__saler=user).count(),
        'total_plans': models.Plan.objects.filter(contract__customer__saler=user).count(),
        'total_services': models.Service.objects.filter(customer__saler=user).count(),
    }

    title = f"我的资料 - {user.username}"
    return render(request, 'user/profile.html', {
        'user': user,
        'user_logs': user_logs,
        'stats': stats,
        'title': title,
    })

def user_profile_edit(request):
    """ 修改个人资料 """
    user = models.User.objects.filter(id=request.info_dict_useid).first()
    if not user:
        return redirect('/login/')

    if request.method == "GET":
        form = ProfileEditModelForm(instance=user)
        return render(request, 'user/profile_edit.html', {'form': form, 'title': '修改个人资料'})

    form = ProfileEditModelForm(data=request.POST, instance=user)
    if form.is_valid():
        form.save()
        return render(request, 'user/profile_success.html', {
            'title': '个人资料修改成功',
            'continue_url': '/user/profile/',
        })
    return render(request, 'user/profile_edit.html', {'form': form, 'title': '修改个人资料'})

def user_change_password(request):
    """ 修改密码 """
    user = models.User.objects.filter(id=request.info_dict_useid).first()
    if not user:
        return redirect('/login/')

    if request.method == "GET":
        form = ChangePasswordForm()
        return render(request, 'user/password_change.html', {'form': form, 'title': '修改密码'})

    form = ChangePasswordForm(data=request.POST)
    if form.is_valid():
        old_password = form.cleaned_data.get('old_password')
        new_password = form.cleaned_data.get('new_password')

        # 验证旧密码
        old_pwd_md5 = md5(old_password)
        if user.password != old_pwd_md5:
            form.add_error('old_password', '旧密码不正确')
            return render(request, 'user/password_change.html', {'form': form, 'title': '修改密码'})

        # 更新密码
        user.password = md5(new_password)
        user.save()
        return render(request, 'user/profile_success.html', {
            'title': '密码修改成功',
            'continue_url': '/user/profile/',
        })

    return render(request, 'user/password_change.html', {'form': form, 'title': '修改密码'})