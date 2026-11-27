# cono_new 项目说明

Django DRF（`api/`）+ Vue3/Element Plus（`frontend/`），老系统在 `cono/`。部署到 NAS 192.168.1.202。

## 目录与脚本

```
cono_new/
├── cono/  cono_new/  manage.py   # 老系统（前后端不分离，8000）
├── api/                          # 新版 API（DRF，8001/8002）
├── frontend/                     # 新版前端（Vue3，5173 / Nginx 8001）
├── deploy/
│   ├── dev.sh                    # 本地一键启动 8000/8001/5173
│   ├── sync.sh                   # NAS 部署：old | new | vue | all（由 scripts/sync.sh nas 调用）
│   ├── nginx-new.conf
│   └── docker-compose.new.yml
└── local_test_settings.py        # 老系统本地设置（去 whitenoise，可选 SQLite）
```

- 本地启动：`./deploy/dev.sh`（不可达生产库时加 `USE_SQLITE=1`）。
  `api/.venv` 与 `frontend/node_modules` 都不入库，首次运行脚本会自动创建并安装依赖。
  `USE_SQLITE=1` 会自动 migrate 并建测试账号 `admin / admin123`。

### 同步入口：仓库根目录 `scripts/sync.sh`
三个方向统一走这一个脚本，不要再用其它方式手工同步：
```bash
./scripts/sync.sh pull      # git → 本地（只快进，分叉时拒绝并提示）
./scripts/sync.sh push      # 本地 → git（提交 + 自动变基 + 推送）
./scripts/sync.sh nas all   # 本地 → NAS（默认 all）
./scripts/sync.sh all       # pull → push → nas
./scripts/sync.sh status    # 本地 / 远程 / NAS 状态
```
`nas` 的目标沿用 `deploy/sync.sh` 的 `old | new | vue | all`。
不带参数运行进入交互菜单，macOS 双击 `Sync.command` 走的就是这条路径。

底层部署细节：
- 老系统：`deploy/sync.sh old`（tar 上传 + `docker restart cono_web`，不重建镜像）
- 新系统：`deploy/sync.sh new`（重建 API 镜像与容器 + 迁移 + 重载 Nginx）
- 只同步前端产物：`deploy/sync.sh vue [文件]`
- 同步会删除 NAS 上本地已不存在的文件；`DRY_RUN=1` 只打印，`PRUNE=0` 关闭删除

### 密码盐：校验用多候选，写入用共享盐
老密码哈希是 `md5(盐 + 明文)`。历史遗留导致同一个 `user` 表里的账号可能由不同盐值
生成：早期账号用 `settings.SECRET_KEY` 的默认值，后来部署脚本又注入
`nas-cono-deploy-key-2026`。**盐值不一致会表现为"用户名或密码错误"，页面上看不出原因。**

现在由 `cono/tools/password.py` 统一处理，不要在各处手写 `md5(...)` 比对：
- `verify_password(stored, 明文)`：按 `candidate_salts()` 逐个尝试，命中任一即通过；
  非 32 位十六进制时按明文兜底比对。登录、改密码校验旧密码都必须用它。
- `hash_password(明文)`：写入用 `shared_salt()`，即 `LEGACY_SECRET_KEY or SECRET_KEY`。
  不能用新 API 自己的 `SECRET_KEY`——那是新系统独有的值，老系统不认识，
  写进去的密码在老系统永远登不上。

`dev.sh` 不再强推某个盐值（只在用户显式设置 `DJANGO_SECRET_KEY` 时才注入），
避免把一批历史账号锁死。`docker-compose.new.yml` / `sync.sh` 的 `LEGACY_SECRET_KEY`
仍需与老系统 `SECRET_KEY` 一致，那是写入时用的共享盐。

另外 `local_test_settings.py` 不设默认 SQLite 路径：空库没有 `user` 表，同样表现为密码错误。

### 登录失败先跑诊断
```bash
# 在仓库根目录，用你的真实账号
api/.venv/bin/python manage.py diagnose_login <用户名> <密码> --settings=local_test_settings
```
它会打印：连的是哪个库、`password` 字段存的是明文还是 md5、各候选盐算出的哈希。
结论含义：
- `库中哈希由「X」生成，已包含在候选盐列表中` → 能正常登录；若仍失败是残留进程或旧代码。
- `所有候选盐都对不上` → 哈希由未知盐生成，把该盐加入 `candidate_salts()` 或重设密码。
- `库里是明文密码` → 登录侧有明文兜底能登，但建议用修改密码功能重设为 md5。

## 本地验证环境

- 前端 dev server：`cd frontend && npm run dev`（5173）
- 后端：`api/` 下用 `.venv`，SQLite 测试库路径 `/workspace/project/my-ai-archive/local_cono_test/cono_local.sqlite3`
  （环境变量 `USE_SQLITE=1`、`CONO_LOCAL_DB_PATH=...`、`DJANGO_SETTINGS_MODULE=cono_api.settings`）
- 模型来自 `cono` 包（与老程序共用）。注意字段名：`Customer.company_name`（不是 `name`）、
  `Invoice.invoice_man` 必填、`Collection.collection_method` 是数字。
- 浏览器验证：`playwright-core` 装于 `/tmp`，浏览器 `/usr/bin/chromium`，JWT 从 `/tmp/token.json` 读取后写入 localStorage。

## 样式约定与陷阱

- 主题色：`--el-color-primary: #0078e0`（`--navy-500`），成功绿 `#67c23a`。
- **`App.vue` 的 `<style>` 是全局的（非 scoped）**，其中 `.el-popper` 的卡片样式会命中所有浮层。
  深色 tooltip（`show-overflow-tooltip` 产生的 `.el-popper.is-dark`）默认是深底白字，
  被这条规则刷成白底后会变成「白底白字」的空白漂浮块。改浮层样式时务必用
  `.el-popper:not(.is-dark)` 排除深色浮层。
- 深色 tooltip 默认没有 `max-width`，超长文本会撑成横跨屏幕的宽条，需自行限制宽度并允许换行。
- `el-progress` 的 `status="success"` 会把百分比文字替换成对勾图标；需要「保留数字且变色」时
  改用 `color` prop，并单独覆盖 `.el-progress__text` 的颜色。
- 表格截断依赖列上的 `show-overflow-tooltip`；`op-cell`（操作列）的 cell 也会带 `el-tooltip` 类但不会弹窗。
- 验收脚本判定「换行/截断」时，`el-progress` 单元格会因行盒亚像素出现 `scrollHeight > clientHeight` 的误报，
  需结合文字实际渲染高度判断。

## 角色与权限

- 角色来源是 `auth_role` 表（`AuthRole`），`User.role` 只是 key，**没有 choices 校验**。
  内置角色只有 `admin` / `upkeeper`（`BUILTIN_ROLE_KEYS`），其余角色可删。
- 新用户默认角色由 `default_role_key()` 决定，固定返回内置的 `upkeeper`（它会先调用
  `ensure_default_roles()` 保证角色存在）；注册、新建用户（新旧系统）都必须走它，不要硬编码角色名。
  不按「权限条数最少」动态挑选：条数会随管理员调整而变，且 finance 之类角色条数少却掌握金额数据。
- `admin` 权限/菜单由 `sync_admin_role()` 与 settings 对齐；权限管理页对 admin 只允许改中文名。
- 删除角色前必须先清空该角色下的用户（后端会拒绝），不会自动改用户角色。
- **权限解析 fail-closed**：`get_role_permissions()` / `get_effective_menus()` 先读 `auth_role`，
  查不到时**只有内置角色**（`BUILTIN_ROLE_KEYS`）回退到 `settings.CONO_PERMISSION` / `CONO_MENU`；
  非内置角色直接返回空集合。否则删掉的角色会因 settings 里还留着同名默认配置而继续生效，
  等于「删除角色」收不回权限。老系统 `cono/tools/auth_profile.py` 与新系统
  `api/core/permissions.py` 两处必须同步修改，否则两端行为不一致。
- 角色被删后仍可能有账号指向它（历史数据/导入）：权限管理页会把该角色作为禁用的占位项
  显示为「XX（角色已删除）」，避免下拉静默落到第一个角色上；管理员选个新角色保存即可恢复。
- **自助注册默认关闭**（`settings.CONO_ALLOW_REGISTER`，环境变量 `CONO_ALLOW_REGISTER=true` 可临时开放）。
  老系统 `/register/`、新系统 `/api/auth/register/` 都会拒绝，账号只能由管理员在用户管理里创建；
  匿名部门接口 `/api/auth/departments/` 已随注册页一起移除。原因：最低权限的 upkeeper 仍带
  `user_reset`，开放注册等于让局域网内任何人重置管理员密码。

## 数据导出

导出接口需要鉴权，前端下载必须带 token；后端各 `export` action 需调用 `filter_queryset`。

## 老系统本地调试

- `api/.venv` 没装 `whitenoise`/`mysqlclient`，直接用 `cono_new.settings` 会 `ModuleNotFoundError`。
  用仓库根目录的 `local_test_settings.py`：它去掉 whitenoise，并在未设置
  `CONO_LOCAL_DB_PATH` 时退回 SQLite。启动加 `--settings=local_test_settings`。
- `DEBUG=False` 时 Django 用 `cached.Loader`，改模板后**必须重启进程**才生效，
  `--noreload` 下尤其容易误判「代码没改对」。
- 登录有图形验证码，浏览器测试可直接造 session 绕过：
  `SessionStore()` 写 `session['info']={'id','username','role'}` 后 `create()`，把 key 作为 `sessionid` cookie。
- 老系统部署走 `./deploy/sync.sh old`（tar 上传 + `docker restart cono_web`，不重建镜像）；
  新系统部署走 `./deploy/sync.sh new`。

## 公告附件

- 附件表 `announcement_attachment`，下载地址用 `token`（uuid4）而非公告 id——公告未保存时
  就要能上传并插入链接。`AnnouncementAttachment.download_path` 只给 `attachment/<token>/download/`，
  前缀由两端各自拼：新版 `/api/announcement/...`（8001），老版 `/announcement/...`（8000）。
- **绑定规则**：保存公告时按两个来源回填 `announcement`——正文里的 `/attachment/<token>/download/`
  链接，以及前端/表单显式提交的 `attachment_tokens`。只绑定 `announcement IS NULL` 或本条公告
  自己的附件，防止把别人公告的附件抢过来。前端必须传 `attachment_tokens`，否则用户「上传了但没
  插链接」时文件会变成孤儿草稿。
- **下载免登录**：正文里是普通 `<a>`，浏览器不会带 Authorization/session。新版 `download_attachment`
  用 `permission_classes=[]`；老版在 `AuthMiddleware._is_attachment_download` 里放行。token 不可猜，
  等价于能力链接。公告下架/软删后两端都返回 404。
- 老版正文若引用了新版 `/api/announcement/...` 地址，`layout.html` 的 `linkify` 会改写成
  `/announcement/...`，否则 8000 上点开 404。
- 草稿附件（`announcement IS NULL`）超过 24 小时由 `manage.py cleanup_announcement_attachments`
  清理，支持 `--dry-run`、`--hours`。
- 新版前端：`AnnouncementContent.vue`（正文链接识别）与 `AnnouncementAttachmentList.vue`（附件区，
  按扩展名配色）挂在 `AnnouncementBell.vue` 详情弹窗里；`AnnouncementList.vue` 管理页负责上传、
  插入链接、草稿/已发布附件列表。
