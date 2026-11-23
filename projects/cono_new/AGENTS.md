# cono_new 项目说明

Django DRF（`api/`）+ Vue3/Element Plus（`frontend/`）。部署到 NAS 192.168.1.202，部署脚本 `start.sh`。

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

## 数据导出

导出接口需要鉴权，前端下载必须带 token；后端各 `export` action 需调用 `filter_queryset`。
