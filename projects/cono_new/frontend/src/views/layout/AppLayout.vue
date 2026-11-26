<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="header-left">
        <button class="hamburger" @click="toggleMobileMenu" aria-label="菜单">
          <el-icon><Menu /></el-icon>
        </button>
        <div class="logo-wrap">
          <img src="/logo.png" class="logo" alt="洛阳科诺" />
          <div class="brand">
            <span class="title">洛阳科诺工业设备有限公司</span>
            <span class="title-sub">智能管理平台</span>
          </div>
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
              <el-dropdown-item command="edit-profile">修改资料</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>注销</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container>
      <el-aside width="224px" class="aside" :class="{ 'aside-mobile-open': mobileMenuOpen }">
        <div class="aside-scroll">
          <el-menu :default-active="$route.path" router class="menu" collapse-width="224" @select="closeMobileMenu">
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon><span>首页</span>
            </el-menu-item>
            <el-menu-item v-for="p in PINNED_ITEMS" :key="p.path" :index="p.path">
              <el-icon><component :is="p.icon" /></el-icon><span>{{ p.title }}</span>
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
    <div class="mobile-overlay" v-if="mobileMenuOpen" @click="closeMobileMenu"></div>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { legacyAppUrl } from '../../utils/legacyApp'
import {
  HomeFilled, ArrowDown, Switch, Menu,
} from '@element-plus/icons-vue'
import { SIDEBAR_ITEMS, MENU_PERM as menuPerm, PINNED_ITEMS } from '../../config/menu'

const router = useRouter()
const userStore = useUserStore()
const user = computed(() => userStore.user)
const mobileMenuOpen = ref(false)

const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const closeMobileMenu = () => { mobileMenuOpen.value = false }



const allowedTitles = computed(() => {
  const s = new Set()
  ;(user.value?.menus || userStore.menus || []).forEach(m => {
    const t = typeof m === 'string' ? m : m?.title || m?.url
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

const goLegacy = () => { window.location.href = legacyAppUrl }
const handleCommand = (cmd) => {
  if (cmd === 'logout') { userStore.logout(); router.push('/login') }
  else if (cmd === 'profile') { router.push('/user/me') }
  else if (cmd === 'edit-profile') { router.push('/user/profile/edit') }
  else if (cmd === 'password') { router.push('/user/profile/password') }
}
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

/* ── 顶部导航栏：NAURA 深海军蓝渐变 + 底部光带 ── */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 22px 0 16px;
  height: 66px;
  flex-shrink: 0;
  background: linear-gradient(120deg, var(--navy-900) 0%, var(--navy-800) 55%, #0a3f78 100%);
  box-shadow: 0 1px 3px rgba(15,40,70,0.16), 0 4px 20px rgba(0,31,63,0.10);
  position: relative;
  z-index: 100;
}
.header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--navy-400), transparent);
  opacity: 0.55;
  box-shadow: 0 0 12px rgba(0,120,224,0.35);
}
.header-left { display: flex; align-items: center; height: 100%; }

/* 汉堡菜单按钮：桌面端隐藏，手机端显示 */
.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255,255,255,0.08);
  border-radius: var(--radius-md);
  color: #ffffff;
  cursor: pointer;
  margin-right: 6px;
  flex-shrink: 0;
}
.hamburger:hover { background: rgba(255,255,255,0.18); }

/* ── 左上角 Logo 区：深蓝顶栏上以白色呈现品牌图形 ── */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  padding: 0 18px 0 6px;
  transition: transform .2s ease;
}
.logo-wrap:hover { transform: translateY(-1px); }
.logo {
  height: 50px;
  width: auto;
  max-width: 190px;
  object-fit: contain;
  /* 把深蓝/青蓝 logo 转成纯白，与深蓝顶栏形成高对比 */
  filter: brightness(0) invert(1);
  display: block;
}
.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  line-height: 1.15;
  padding-left: 14px;
  border-left: 1px solid rgba(0,120,224,0.3);
}
.title {
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 2px;
  text-shadow: 0 0 22px rgba(0,120,224,0.55);
  white-space: nowrap;
}
.title-sub {
  font-size: 12px;
  font-weight: 700;
  color: var(--navy-200);
  letter-spacing: 5px;
  white-space: nowrap;
}
.header-right { display: flex; align-items: center; gap: 14px; }

/* ── 「返回老版」按钮：霓虹蓝渐变胶囊，深蓝顶栏上醒目 ── */
.btn-back {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border: 1px solid rgba(0,120,224,0.7) !important;
  color: #ffffff !important;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: var(--radius-md) !important;
  padding: 6px 16px !important;
  height: auto !important;
  box-shadow: 0 0 18px rgba(0,120,224,0.45) !important;
  transition: all .25s;
}
.btn-back:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 28px rgba(0,120,224,0.7) !important;
  background: linear-gradient(135deg, var(--navy-400), var(--navy-600)) !important;
}

/* ── 用户信息：白字，避免深色文字在深蓝顶栏上看不见 ── */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #ffffff;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: background .2s;
}
.user-info:hover { background: rgba(255,255,255,0.08); }
.user-name { font-size: 13px; color: #ffffff; font-weight: 500; }
.avatar-blue {
  background: linear-gradient(135deg, #ffffff, var(--navy-200)) !important;
  font-weight: 600;
  font-size: 13px;
  color: var(--navy-800);
  box-shadow: 0 0 14px rgba(255,255,255,0.4);
}

/* ── 主体容器：左右布局，高100% ── */
.layout > .el-container {
  flex: 1;
  overflow: hidden;
}

/* ── 左侧边栏：纯白底 + 深蓝菜单 ── */
.aside {
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  box-shadow: 1px 0 12px rgba(15,40,70,0.03);
}
.aside::-webkit-scrollbar { width: 4px; }
.aside::-webkit-scrollbar-track { background: transparent; }
.aside::-webkit-scrollbar-thumb { background: rgba(0,120,224,0.25); border-radius: 2px; }

.aside-scroll { padding: 8px 0; }

.menu { border-right: none; background: transparent !important; }
.menu .el-menu-item {
  height: 42px;
  line-height: 42px;
  margin: 3px 10px;
  border-radius: var(--radius-md);
  color: var(--text-sub) !important;
  font-size: 13.5px;
  transition: all var(--dur) var(--ease);
}
.menu .el-menu-item:hover {
  background: var(--navy-50) !important;
  color: var(--navy-600) !important;
}
.menu .el-menu-item.is-active {
  background: linear-gradient(90deg, rgba(0,120,224,0.10), rgba(0,120,224,0.02)) !important;
  color: var(--navy-700) !important;
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--navy-500);
}
.menu .el-menu-item .el-icon { color: var(--text-dim); font-size: 16px; transition: color var(--dur) var(--ease); }
.menu .el-menu-item:hover .el-icon { color: var(--navy-500); }
.menu .el-menu-item.is-active .el-icon { color: var(--navy-600); }
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
.main::-webkit-scrollbar-thumb { background: rgba(0,120,224,0.25); border-radius: 3px; }
.main::-webkit-scrollbar-thumb:hover { background: rgba(0,120,224,0.45); }

.main-inner {
  padding: 24px 28px 32px;
  min-height: 100%;
  font-size: inherit;
}

/* ── 窄屏适配：Logo 区随视口适当收小，避免拥挤 ── */
@media (max-width: 900px) {
  .header { height: 64px; padding: 0 12px; }
  .logo-wrap { padding: 0 10px 0 2px; gap: 8px; }
  .logo { height: 40px; max-width: 150px; padding: 4px 8px; }
  .brand { padding-left: 8px; }
  .title { font-size: 16px; letter-spacing: 0.5px; }
  .title-sub { font-size: 11px; letter-spacing: 2px; }
}

/* ── 手机端（≤768px）：汉堡菜单 + 抽屉式侧边栏 ── */
@media (max-width: 768px) {
  .layout { display: flex; flex-direction: column; height: 100vh; }

  .header {
    height: 56px;
    padding: 0 10px;
    flex-shrink: 0;
  }
  .hamburger {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: none;
    background: rgba(255,255,255,0.08);
    border-radius: var(--radius-md);
    color: #ffffff;
    cursor: pointer;
    margin-right: 6px;
    flex-shrink: 0;
  }
  .hamburger:hover { background: rgba(255,255,0.18); }

  .logo-wrap { padding: 0 6px 0 0; gap: 6px; }
  .logo { height: 34px; max-width: 120px; padding: 0; }
  .brand { padding-left: 6px; }
  .title { font-size: 14px; letter-spacing: 0.5px; }
  .title-sub { font-size: 10px; letter-spacing: 1px; }

  .header-right { gap: 8px; }
  .user-name { display: none; }
  .avatar-blue { width: 30px; height: 30px; font-size: 12px; }
  .btn-back { font-size: 11px; padding: 4px 10px !important; }

  /* 侧边栏在手机端默认隐藏，仅在汉堡点击后滑入 */
  .aside {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 240px;
    z-index: 2000;
    transform: translateX(-100%);
    transition: transform .28s ease;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.1), 0 8px 32px rgba(0,0,0,0.3);
  }
  .aside.aside-mobile-open { transform: translateX(0); }

  .mobile-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 1999;
    backdrop-filter: blur(2px);
  }

  .main { padding: 0 !important; }
  .main-inner { padding: 12px 14px 16px; }

  .menu .el-menu-item { height: 40px; line-height: 40px; font-size: 13px; margin: 2px 6px; }
  .menu .el-menu-item .el-icon { font-size: 15px; }
}
</style>
