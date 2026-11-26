"""老版本地开发设置。

只做两件事，数据库与密码盐值都沿用 cono_new.settings，保证与生产一致：
  1. 去掉 whitenoise 中间件（api/.venv 没装它）
  2. 可选：CONO_LOCAL_DB_PATH 指向 SQLite 时改用它

注意：不要在这里默认退回某个 SQLite 文件。空库没有 user 表，登录会直接报
"用户名或密码错误"，看起来像密码错了，实际是连错了库。
"""
import os

from cono_new.settings import *  # noqa: F401,F403

# api/.venv 没装 whitenoise，中间件里有它会直接 ModuleNotFoundError
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]  # noqa: F405

# 显式指定 SQLite 副本时才切换；否则沿用 cono_new.settings 的 MySQL 配置
if os.environ.get('CONO_LOCAL_DB_PATH'):
    DATABASES = {  # noqa: F405
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ['CONO_LOCAL_DB_PATH'],
        }
    }
