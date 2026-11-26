from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django import forms
from django.contrib import messages
from io import BytesIO
from datetime import date
from cono.tools.helper import check_code
from cono import models
from cono.tools.bootstrap import BootStrapForm
from cono.tools.form import RegisterUserModelForm
from cono.tools.encrypt import md5
from cono.tools.auth_profile import default_role_key

class LoginForm(BootStrapForm):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput,
        required=True
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(render_value=True),
        required=True
    )

    code = forms.CharField(
        label="验证码",
        widget=forms.TextInput,
        required=True
    )
    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        if not pwd:
            raise forms.ValidationError("密码不能为空")
        return md5(pwd)
def login(request):
    """ 登录 """
    title = "登录"
    if request.session.get("info"):
        messages.success(request, "你已登录，正在返回首页")
        return redirect('/')

    if request.method == "GET":
        form = LoginForm()
        return render(request, 'login.html', {'form': form ,'title': title})

    form = LoginForm(data=request.POST)

    if not form.is_valid():
        return render(request, 'login.html', {'form': form})

    user_input_code = form.cleaned_data.pop('code')
    code = request.session.get('image_code', "")
    if code.upper() != user_input_code.upper():
        form.add_error("code", "验证码错误")
        return render(request, 'login.html', {'form': form})
    user_object = models.User.objects.filter(**form.cleaned_data).first()
    if not user_object:
        return render(request, 'login.html', {'form': form, 'error': "用户名或密码错误"})

    # 用户名和密码正确，写入session
    request.session["info"] = {'id': user_object.id, 'username': user_object.username, 'role': user_object.role}
    # session有效期7天
    request.session.set_expiry(60 * 60 * 24 * 1 * 7)

    return redirect('/')

def image_code(request):
    """ 生成图片验证码 """
    img, code_string = check_code()
    # 存入session用于后续校验
    request.session['image_code'] = code_string
    # 验证码60秒过期
    request.session.set_expiry(60)

    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

def logout(request):
    """ 注销 """
    request.session.clear()

    return redirect('/login/')

def register(request):
    """ 注册（默认关闭，需 CONO_ALLOW_REGISTER=true 才开放） """
    if not getattr(settings, 'CONO_ALLOW_REGISTER', False):
        return redirect('/login/')
    title = "用户注册"
    if request.method == "GET":
        form = RegisterUserModelForm()
        return render(request, 'register.html', {'form': form, 'title': title})

    form = RegisterUserModelForm(data=request.POST)
    if form.is_valid():
        user_input_code = form.cleaned_data.get('code')
        code = request.session.get('image_code', "")
        if not user_input_code or code.upper() != user_input_code.upper():
            form.add_error('code', '验证码错误')
            return render(request, 'register.html', {'form': form, 'title': title})

        instance = form.save(commit=False)
        instance.role = default_role_key()
        instance.create_date = date.today()
        instance.save()
        return render(request, 'register_success.html', {
            'url_path': '/login/',
        })
    return render(request, 'register.html', {'form': form, 'title': title})