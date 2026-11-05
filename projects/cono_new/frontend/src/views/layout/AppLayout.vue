<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="header-left">
        <div class="logo-wrap">
          <img src="/logo.png" class="logo" alt="Logo" />
          <span class="title">洛阳科诺</span>
          <span class="title-sub">智能管理平台</span>
        </div>
      </div>
      <div class="header-right">
        <el-button type="info" size="small" @click="goLegacy" class="btn-back">
          <el-icon><Switch /></el-icon>&nbsp;返回老版
        </el-button>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" class="avatar-blue">{{ initials }}</el-avatar>
            <span class="user-name">{{ user?.name || user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">我的资料</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>注销</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="224px" class="aside">
        <div class="aside-scroll">
          <el-menu :default-active="$route.path" router class="menu" collapse-width="224">
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon><span>首页</span>
            </el-menu-item>
            <template v-for="m in visibleMenus" :key="m.path">
              <el-menu-item :index="m.path">
                <el-icon><component :is="m.icon" /></el-icon><span>{{ m.title }}</span>
              </el-menu-item>
              <el-divider v-if="m.divider" class="menu-divider" />
            </template>
          </el-menu>
        </div>
      </el-aside>
      <el-main class="main">
        <div class="main-inner">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import {
  HomeFilled, Document, Tools, Money, List, Calendar, Van, User, Files, Goods,
  Box, RefreshLeft, Postcard, Upload, OfficeBuilding, UserFilled, TrendCharts,
  FolderOpened, Clock, Lock, Key, ArrowDown, Switch, Setting, InfoFilled,
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.user)

// 菜单入口所需权限码（与老版 MENU_PERMISSIONS 一致）
const menuPerm = {
  '/contract': ['contract_list'],
  '/service': ['service_list'],
  '/collection': ['collection_list'],
  '/invoice': ['invoice_list'],
  '/plan': ['plan_list'],
  '/delivery': ['delivery_list'],
  '/customer': ['customer_list'],
  '/product-category': ['productcategory_list'],
  '/product': ['product_list'],
  '/servicedetail': ['servicedetail_list'],
  '/return-product': ['return_product_list'],
  '/task': ['task_list'],
  '/product-label': ['productlabel_list'],
  '/contract-file': ['contract_file_list'],
  '/warehouse': ['warehouse_list'],
  '/department': ['department_list'],
  '/user': ['user_list'],
  '/chart': ['chart_list', 'chart_bar', 'chart_bar2', 'chart_pie', 'chart_line', 'highcharts'],
  '/backup': ['backup_database', 'restore_database'],
  '/log': ['get_log'],
  '/company': ['company_show'],
  '/account-vault': ['account_vault_list'],
  '/auth/role': ['auth_role_list', 'auth_user_permission'],
}

// 侧边栏菜单定义（标题与路由权限一一对应）
const SIDEBAR_ITEMS = [
  { path: '/contract', title: '合同管理', icon: Document },
  { path: '/invoice', title: '发票登记', icon: List },
  { path: '/collection', title: '回款登记', icon: Money },
  { path: '/chart', title: '应收应付', icon: TrendCharts },
  { path: '/plan', title: '生产计划', icon: Calendar },
  { path: '/contract-file', title: '资料上传', icon: Upload },
  { path: '/task', title: '派任务单', icon: Calendar },
  { path: '/product-label', title: '产品铭牌', icon: Postcard },
  { path: '/delivery', title: '发货信息', icon: Van },
  { path: '/service', title: '售后服务', icon: Tools },
  { path: '/servicedetail', title: '维修服务', icon: Setting },
  { path: '/return-product', title: '售后返件', icon: RefreshLeft },
  { path: '/product-category', title: '产品分类', icon: Files },
  { path: '/product', title: '产品管理', icon: Goods, divider: true },
  { path: '/department', title: '部门管理', icon: OfficeBuilding },
  { path: '/warehouse', title: '仓库管理', icon: Box },
  { path: '/company', title: '公司信息', icon: InfoFilled },
  { path: '/log', title: '操作日志', icon: Clock },
  { path: '/backup', title: '数据备份', icon: FolderOpened },
  { path: '/account-vault', title: '账号密码', icon: Lock },
  { path: '/auth/role', title: '权限管理', icon: Key, divider: true },
]

// 登录后由后端返回的角色已勾选菜单标题集合（来自 auth_role.menus）
const allowedTitles = computed(() => {
  const s = new Set()
  ;(user.value?.menus || []).forEach(m => {
    const t = typeof m === 'string' ? m : m?.title
    if (t) s.add(t)
  })
  return s
})

const visibleMenus = computed(() => {
  return SIDEBAR_ITEMS.filter(m => menuAllowed(m))
})

const menuAllowed = (m) => {
  // 1) 权限码校验（后端已按角色权限过滤）
  const required = menuPerm[m.path]
  if (required && !(userStore.hasPerm(required[0]) || required.some(c => userStore.hasPerm(c)))) {
    return false
  }
  // 2) 菜单栏目校验：角色勾选集合非空时，必须包含该菜单标题
  const titles = allowedTitles.value
  if (titles.size > 0) {
    return titles.has(m.title)
  }
  return true
}

const initials = computed(() => {
  const name = user.value?.name || user.value?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const goLegacy = () => { window.location.href = 'http://192.168.1.202:8000/' }
const handleCommand = (cmd) => { if (cmd === 'logout') { userStore.logout(); router.push('/login') } }
</script>

<style scoped>
/* ── 整体布局：占满视口高度 ── */
.layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-body);
}

/* ── 顶部导航栏 ── */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 40%, #7dd3fc 100%);
  box-shadow: 0 2px 12px rgba(14,165,233,0.12), 0 1px 0 rgba(255,255,255,0.6) inset;
  position: relative;
  z-index: 100;
}
.header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue-400), transparent);
  opacity: 0.6;
}
.header-left { display: flex; align-items: center; }
.logo-wrap { display: flex; align-items: center; gap: 10px; }
.logo { height: 32px; }
.title {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #0369a1;
  letter-spacing: 2px;
}
.title-sub { font-size: 11px; color: #0284c7; letter-spacing: 1px; }
.header-right { display: flex; align-items: center; gap: 16px; }

.btn-back {
  background: rgba(255,255,255,0.5) !important;
  border: 1px solid rgba(2,132,199,0.25) !important;
  color: #0369a1 !important;
  font-size: 12px;
}
.btn-back:hover {
  background: rgba(255,255,255,0.8) !important;
  border-color: #0284c7 !important;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #0369a1;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background .2s;
}
.user-info:hover { background: rgba(255,255,255,0.4); }
.user-name { font-size: 13px; color: #0369a1; font-weight: 500; }
.avatar-blue {
  background: linear-gradient(135deg, var(--blue-400), var(--blue-600)) !important;
  font-weight: 600;
  font-size: 13px;
  color: #fff;
  box-shadow: 0 0 10px rgba(56,189,248,0.35);
}

/* ── 主体容器：左右布局，高100% ── */
.layout > .el-container {
  flex: 1;
  overflow: hidden;
}

/* ── 左侧边栏 ── */
.aside {
  background: #fff;
  border-right: 1px solid var(--border);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  box-shadow: 2px 0 12px rgba(14,165,233,0.04);
}
.aside::-webkit-scrollbar { width: 4px; }
.aside::-webkit-scrollbar-track { background: transparent; }
.aside::-webkit-scrollbar-thumb { background: var(--blue-200); border-radius: 2px; }

.aside-scroll { padding: 8px 0; }

.menu { border-right: none; background: #fff !important; }
.menu .el-menu-item {
  height: 42px;
  line-height: 42px;
  margin: 2px 8px;
  border-radius: 8px;
  color: var(--text-sub) !important;
  font-size: 13px;
  transition: all .2s;
}
.menu .el-menu-item:hover {
  background: var(--blue-50) !important;
  color: var(--blue-600) !important;
}
.menu .el-menu-item.is-active {
  background: linear-gradient(90deg, var(--blue-100), transparent) !important;
  color: var(--blue-700) !important;
}
.menu .el-menu-item .el-icon { color: var(--blue-500); font-size: 16px; }
.menu-divider { margin: 8px 16px; border-color: var(--border) !important; }

/* ── 右侧主内容区：可滚动 ── */
.main {
  background: var(--bg-body);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 !important;
  flex: 1;
  font-size: 12px;
  color: var(--text-main);
  line-height: 1.5;
}
.main :deep(.el-card), .main :deep(.el-table), .main :deep(.el-form),
.main :deep(.el-button), .main :deep(.el-input__inner), .main :deep(.el-pagination),
.main :deep(.el-descriptions), .main :deep(.el-tag), .main :deep(.el-statistic) {
  font-size: 12px;
}
.main::-webkit-scrollbar { width: 6px; }
.main::-webkit-scrollbar-track { background: transparent; }
.main::-webkit-scrollbar-thumb { background: var(--blue-200); border-radius: 3px; }
.main::-webkit-scrollbar-thumb:hover { background: var(--blue-300); }

.main-inner {
  padding: 20px 24px;
  min-height: 100%;
  font-size: inherit;
}
</style>
