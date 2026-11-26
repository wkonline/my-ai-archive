"""老系统本地开发设置：去掉 api/.venv 里没有的 whitenoise，并默认用 SQLite。

生产部署走 cono_new.settings（Docker 镜像里装了 whitenoise/mysqlclient），不用本文件。
"""
import os

from cono_new.settings import *  # noqa: F401,F403

# api/.venv 没装 whitenoise，中间件里有它会直接 ModuleNotFoundError
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]  # noqa: F405

# 生产库 192.168.1.201 在开发机上通常不可达，未指定路径时退回本地 SQLite
if not os.environ.get('CONO_LOCAL_DB_PATH'):
    DATABASES = {  # noqa: F405
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/cono_local.sqlite3',
        }
    }
