import os
from cono_new.settings import *

# 过滤掉 whitenoise
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]

# 使用 SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/cono_local.sqlite3',
    }
}
