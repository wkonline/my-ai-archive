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
