# 新版前后端分离系统 · 本地开发说明

## 目录结构
```
cono_new/
├── cono/            # 老版 Django app（不动）
├── cono_new/        # 老版 Django 项目（不动）
├── manage.py        # 老版入口（不动）
├── api/             # 新版后端（DRF）
│   ├── .venv/       # 独立虚拟环境
│   ├── cono_api/    # settings/urls/wsgi
│   ├── core/        # 模型/序列化器/视图
│   └── manage.py
├── frontend/        # 新版前端（Vue3 + Element Plus）
│   ├── src/         # 源码
│   ├── dist/        # 构建产物
│   └── package.json
└── deploy/          # 部署配置（暂不上传 NAS）
    ├── docker-compose.new.yml
    ├── nginx-new.conf
    └── sync_new_to_nas.sh
```

## 本地启动
```bash
# 1. 后端 API（端口 8001）
cd api
.venv/bin/python manage.py runserver 8001

# 2. 前端（端口 5173）
cd frontend
npm run dev
# 访问 http://localhost:5173
```

## 测试账号
- 用户名：admin
- 密码：admin123

## 说明
- 本地开发使用 SQLite（api/db.sqlite3），不连线上 MySQL，不影响老版。
- 上线时通过 USE_MYSQL=1 环境变量切换到老版 cono 库。
- 老版代码（cono/、cono_new/、manage.py、sync_to_nas.sh）保持原样，不做任何修改。

## 迁移规则（重要）
表结构只由 `cono/migrations` 管理。`api/core` 没有自己的模型（`core/models.py` 全部
`from cono.models import *`），它的 `core/migrations/0001~0003` 是三个空迁移，只为兼容
记录过这三个版本号的旧库，不产生任何数据库操作。

千万不要在 `api/` 目录下执行 `makemigrations core` 并提交结果：core 检测不到任何模型，
生成的会是 `DeleteModel`，apply 之后会把老版系统正在用的 `contract` / `customer` /
`invoice` 等共享表 DROP 掉。历史上这三个迁移曾重复定义整套表，导致新库 `migrate`
直接报 `table xxx already exists`。模型有改动时，在仓库根目录对 `cono` 生成迁移。

## 路径约定（重要）
新版 `BASE_DIR` 是 `api/`，老版是仓库根，两者容器里都挂在 `/app`。
所以凡是"两边要共享"的目录都必须显式指向仓库根，不能用 `BASE_DIR`：

| 目录 | 老版 | 新版（settings 里显式指定） | NAS 挂载 |
|------|------|------------------------------|----------|
| media | `BASE_DIR/media` = `/app/media` | `PROJECT_ROOT/media` = `/app/media` | `/volume1/docker/cono_media` |
| backups | `BASE_DIR/backups` = `/app/backups` | `BACKUP_DIR` = `/app/backups` | `/volume1/docker/cono_backups` |

两者都可用 `DJANGO_MEDIA_ROOT` / `DJANGO_BACKUP_DIR` 覆盖。曾出现的问题：
新版用 `BASE_DIR/media` 会落到 `/app/api/media`，Nginx 的 `/media/` alias 读不到，
上传的附件 404；新版备份同样会落到 `/app/api/backups`，网页备份管理看不到定时备份。

## 备份容器
`cono_backup` 用 `cono_api` 镜像，必须执行 `python api/manage.py backup_database`。
该镜像只有 PyMySQL，跑根目录 `manage.py`（`cono_new.settings`，依赖 mysqlclient）
会直接 `ImproperlyConfigured: Did you install mysqlclient?` 而静默失败。
