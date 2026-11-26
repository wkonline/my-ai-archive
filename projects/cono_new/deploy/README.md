# 新版前后端分离系统 · 本地开发说明

## 目录结构
```
cono_new/
├── cono/            # 老版 Django app
├── cono_new/        # 老版 Django 项目（settings/urls/wsgi）
├── manage.py        # 老版入口
├── local_test_settings.py  # 老版本地设置（去 whitenoise + SQLite）
├── api/             # 新版后端（DRF）
│   ├── .venv/       # 独立虚拟环境
│   ├── cono_api/    # settings/urls/wsgi
│   ├── core/        # 模型/序列化器/视图
│   └── manage.py
├── frontend/        # 新版前端（Vue3 + Element Plus）
│   ├── src/         # 源码
│   ├── dist/        # 构建产物（不入库）
│   └── package.json
└── deploy/          # 部署与本地启动
    ├── dev.sh               # 本地一键启动 8000/8001/5173
    ├── sync.sh              # NAS 部署：old | new | vue | all
    ├── nginx-new.conf
    └── docker-compose.new.yml
```

## 本地启动
```bash
./deploy/dev.sh              # 一键启动三个服务（已在运行的会跳过）
USE_SQLITE=1 ./deploy/dev.sh # 生产库不可达时用本地 SQLite
```
等价的手动方式：
```bash
# 1. 后端 API（端口 8001）
cd api
.venv/bin/python manage.py runserver 8001

# 2. 前端（端口 5173）
cd frontend
npm run dev
# 访问 http://localhost:5173
```

## 部署到 NAS
```bash
./deploy/sync.sh old          # 老版系统（8000）
./deploy/sync.sh new          # 新版系统（8001 → API 8002）
./deploy/sync.sh vue [文件]   # 只同步前端产物
./deploy/sync.sh all          # 先 old 再 new
```

## 测试账号
- 用户名：admin
- 密码：admin123

## 说明
- 本地开发使用 SQLite（api/db.sqlite3），不连线上 MySQL，不影响老版。
- 上线时通过 USE_MYSQL=1 环境变量切换到老版 cono 库。
- 老版代码（`cono/`、`cono_new/`、`manage.py`）由老系统维护，新系统只读复用其模型与 settings。

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
