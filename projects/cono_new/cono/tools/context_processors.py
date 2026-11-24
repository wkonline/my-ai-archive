from django.conf import settings


def new_app_url(request):
    """向所有模板注入新版（尝鲜版）前端首页地址与自助注册开关。"""
    return {
        'new_app_url': settings.NEW_APP_URL,
        'allow_register': getattr(settings, 'CONO_ALLOW_REGISTER', False),
    }
