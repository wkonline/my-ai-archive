"""
新版前后端分离 - API 配置
本地开发直接连接真实 MySQL（老版 cono 库），不用 SQLite 测试库。
如需切回 SQLite 测试库，设 USE_SQLITE=1。
"""
import os
import sys
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# 本项目 core 复用老版 cono 应用（from cono.models import *），
# 而 gunicorn/manage.py 的工作目录是 api/，需要把仓库根目录加入模块搜索路径。
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-$_+6ouqgn0hxgt19h&!1yh@^=@@x4xnzxg!zb=vyeg513kv$(j')
# 老版系统（cono_web）的 SECRET_KEY：老密码哈希 = md5(这个值 + 明文密码)。
# 新版 API 校验老账号必须用同一个盐值，否则线上所有账号都提示“用户名或密码错误”。
LEGACY_SECRET_KEY = os.environ.get(
    'LEGACY_SECRET_KEY',
    'django-insecure-$_+6ouqgn0hxgt19h&!1yh@^=@@x4xnzxg!zb=vyeg513kv$(j',
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'cono.apps.ConoConfig',   # 老版模型（api.core.models 从这里导入）
    'api.core.apps.CoreConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cono_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cono_api.wsgi.application'

# 本地开发：直接连接真实 MySQL（复用老版 cono 库）
# 设 USE_SQLITE=1 可切回 SQLite 测试库
if os.environ.get('USE_SQLITE', '') == '1':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    import pymysql
    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DJANGO_DB_NAME', 'cono'),
            'USER': os.environ.get('DJANGO_DB_USER', 'cono'),
            'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'cono2024'),
            'HOST': os.environ.get('DJANGO_DB_HOST', '192.168.1.201'),
            'PORT': int(os.environ.get('DJANGO_DB_PORT', '3306')),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 老版权限/菜单配置（从 cono_new/settings.py 复制，供权限管理栏目使用）
# 直接引用老项目 settings 文件以保持一致，避免维护两份。
import importlib.util as _ilu
import pathlib as _pl
_old_settings_path = _pl.Path(__file__).resolve().parent.parent.parent / 'cono_new' / 'settings.py'
try:
    _spec = _ilu.spec_from_file_location('_old_cono_settings', _old_settings_path)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    CONO_PERMISSION = getattr(_mod, 'CONO_PERMISSION', {})
    CONO_MENU = getattr(_mod, 'CONO_MENU', {})
except Exception as _e:
    CONO_PERMISSION = {}
    CONO_MENU = {}

# JWT 认证
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'api.core.authentication.CoreUserJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS（本地 Vite dev 跨域）
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# 缓存：验证码等跨进程共享数据。
# gunicorn 起多个 worker 时，进程内字典无法共享，会导致“验证码错误”随机出现；
# 这里用文件缓存（同一容器内各 worker 共享 /tmp），无需额外 Redis。
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.environ.get('DJANGO_CACHE_DIR', '/tmp/cono_django_cache'),
        'TIMEOUT': 300,
    }
}
