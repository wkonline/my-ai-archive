<template>
  <div class="sitemap-page">
    <div class="map-head">
      <div>
        <h2><el-icon><MapLocation /></el-icon>网站地图</h2>
        <p class="sub">
          共 {{ totalCount }} 个功能入口，其中 {{ accessibleCount }} 个对当前账号开放
          <span v-if="lockedCount">· {{ lockedCount }} 个需授权</span>
        </p>
      </div>
      <div class="head-actions">
        <el-tag v-if="isAdmin" type="success" size="small" effect="plain">管理员 · 全部可见</el-tag>
        <el-button size="small" @click="goLegacy">
          <el-icon><Switch /></el-icon>&nbsp;前往老系统
        </el-button>
      </div>
    </div>

    <div class="group-grid">
      <div class="map-group" v-for="group in groupedMenus" :key="group.name">
        <div class="group-head">
          <span>{{ group.name }}</span>
          <span class="count">{{ group.items.filter(i => i.allowed).length }}/{{ group.items.length }}</span>
        </div>
        <div class="group-body">
          <component
            :is="item.allowed ? 'router-link' : 'div'"
            v-for="item in group.items"
            :key="item.path"
            :to="item.allowed ? item.path : undefined"
            class="map-item"
            :class="{ locked: !item.allowed }"
          >
            <div class="item-main">
              <span class="item-icon"><el-icon><component :is="item.icon" /></el-icon></span>
              <div class="item-text">
                <span class="item-title">
                  {{ item.title }}
                  <el-icon v-if="!item.allowed" class="lock-icon"><Lock /></el-icon>
                </span>
                <span class="item-path">{{ item.path }}</span>
              </div>
            </div>
            <div class="item-meta" v-if="item.allowed">
              <span class="tag" v-if="item.readonly">查询页</span>
              <template v-else>
                <span class="tag">列表</span>
                <span class="tag">新增</span>
                <span class="tag">编辑</span>
              </template>
            </div>
            <div class="item-subpages" v-if="item.allowed && item.subpages.length">
              <router-link
                v-for="sub in item.subpages"
                :key="sub.path"
                :to="sub.path"
                class="subpage"
              >{{ sub.label }}</router-link>
            </div>
          </component>
        </div>
      </div>
    </div>

    <div class="map-foot">
      <div class="foot-note">
        <el-icon><InfoFilled /></el-icon>
        <span>地图只展示当前账号可访问的入口。标注锁定图标的栏目需联系管理员授权，授权后重新登录即可看到。</span>
      </div>
      <div class="foot-note">
        <el-icon><InfoFilled /></el-icon>
        <span>老系统（:8000）菜单与新版基本一致，但「售后流转」仅在新版提供，老版没有对应页面。</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { legacyAppUrl } from '../../utils/legacyApp'
import { MapLocation, Switch, Lock, InfoFilled } from '@element-plus/icons-vue'
import {
  SIDEBAR_ITEMS, PINNED_ITEMS, MENU_GROUPS, MENU_GROUP_ORDER, MENU_PERM, MENU_SUBPAGES, READONLY_PAGES,
} from '../../config/menu'

// 地图要展示全部入口，含常驻的「网站地图」自身
const ALL_ITEMS = [...PINNED_ITEMS, ...SIDEBAR_ITEMS]

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => (userStore.user?.role || '') === 'admin')

// 与侧边栏 menuAllowed 同源的两层校验：权限码 + 角色勾选的菜单栏目
const allowedTitles = computed(() => {
  const set = new Set()
  ;(userStore.user?.menus || userStore.menus || []).forEach(m => {
    const t = typeof m === 'string' ? m : m?.title || m?.url
    if (t) set.add(t)
  })
  return set
})

const pinnedPaths = new Set(PINNED_ITEMS.map(i => i.path))

const isAllowed = (item) => {
  // 常驻入口（网站地图自身）不走角色菜单与权限码，与侧边栏保持一致
  if (pinnedPaths.has(item.path)) return true
  const required = MENU_PERM[item.path]
  if (required && !required.some(code => userStore.hasPerm(code))) return false
  const titles = allowedTitles.value
  if (titles.size > 0) return titles.has(item.title)
  return true
}

const groupedMenus = computed(() => {
  const decorate = (item) => ({
    ...item,
    allowed: isAllowed(item),
    readonly: READONLY_PAGES.includes(item.path),
    subpages: MENU_SUBPAGES[item.path] || [],
  })
  const byTitle = new Map(ALL_ITEMS.map(i => [i.title, decorate(i)]))

  const groups = MENU_GROUP_ORDER.map(name => ({
    name,
    items: (MENU_GROUPS[name] || []).map(t => byTitle.get(t)).filter(Boolean),
  }))
  const grouped = new Set(MENU_GROUP_ORDER.flatMap(n => MENU_GROUPS[n] || []))
  const rest = ALL_ITEMS.filter(i => !grouped.has(i.title)).map(decorate)
  if (rest.length) groups.push({ name: '其他', items: rest })
  return groups.filter(g => g.items.length)
})

const totalCount = computed(() => ALL_ITEMS.length)
const accessibleCount = computed(() => groupedMenus.value.flatMap(g => g.items).filter(i => i.allowed).length)
const lockedCount = computed(() => totalCount.value - accessibleCount.value)

const goLegacy = () => { window.location.href = legacyAppUrl }
</script>

<style scoped>
.sitemap-page { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }

.map-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; margin-bottom: 20px;
}
.map-head h2 {
  display: flex; align-items: center; gap: 8px; margin: 0 0 6px;
  font-size: 20px; font-weight: 680; color: var(--text-main); letter-spacing: -0.2px;
}
.map-head h2 .el-icon { color: var(--navy-500); font-size: 22px; }
.map-head .sub { margin: 0; font-size: 12.5px; color: var(--text-sub); }
.head-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.group-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px; align-items: start;
}
.map-group {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-sm);
  transition: box-shadow var(--dur) var(--ease), border-color var(--dur) var(--ease);
}
.map-group:hover { box-shadow: var(--shadow-md); border-color: var(--border-bright); }
.group-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: var(--bg-subtle);
  border-bottom: 1px solid var(--border-soft);
  font-size: 13px; font-weight: 650; color: var(--navy-800); letter-spacing: .2px;
}
.group-head .count {
  font-size: 11px; font-weight: 600; color: var(--text-dim);
  background: #fff; border: 1px solid var(--border);
  border-radius: 999px; padding: 1px 8px; font-variant-numeric: tabular-nums;
}
.group-body { padding: 4px 0; }

.map-item {
  display: block; padding: 10px 16px; text-decoration: none;
  border-bottom: 1px solid var(--border-soft);
  transition: background var(--dur) var(--ease);
}
.map-item:last-child { border-bottom: none; }
.map-item:hover { background: var(--navy-50); }
.map-item.locked { opacity: .48; cursor: not-allowed; }
.map-item.locked:hover { background: transparent; }

.item-main { display: flex; align-items: center; gap: 9px; }
.item-icon {
  width: 28px; height: 28px; flex-shrink: 0; border-radius: var(--radius-sm);
  background: var(--navy-50); color: var(--navy-600);
  display: flex; align-items: center; justify-content: center; font-size: 14px;
  transition: all var(--dur) var(--ease);
}
.map-item:hover .item-icon { background: var(--navy-500); color: #fff; }
.map-item.locked .item-icon { background: #f1f5f9; color: #94a3b8; }
.item-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.item-title {
  display: flex; align-items: center; gap: 5px;
  font-size: 13px; font-weight: 600; color: var(--text-main);
}
.map-item.locked .item-title { color: var(--text-dim); }
.lock-icon { font-size: 11px; color: #94a3b8; }
.item-path {
  font-family: "SF Mono", "JetBrains Mono", Consolas, monospace;
  font-size: 10.5px; color: var(--navy-600); word-break: break-all;
}
.map-item.locked .item-path { color: var(--text-dim); }

.item-meta { display: flex; gap: 5px; margin: 7px 0 0 37px; }
.tag {
  font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 4px;
  background: var(--navy-50); color: var(--navy-700); border: 1px solid var(--navy-100);
}

.item-subpages { display: flex; flex-wrap: wrap; gap: 5px; margin: 7px 0 0 37px; }
.subpage {
  font-size: 10.5px; padding: 1px 8px; border-radius: 999px;
  background: #f5f3ff; color: #5b21b6; border: 1px solid #ddd6fe;
  text-decoration: none; transition: all var(--dur) var(--ease);
}
.subpage:hover { background: #ede9fe; border-color: #c4b5fd; }

.map-foot {
  margin-top: 20px; padding: 14px 16px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-left: 3px solid var(--navy-500); border-radius: var(--radius-md);
  display: flex; flex-direction: column; gap: 9px;
}
.foot-note {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: 12px; color: var(--text-sub); line-height: 1.65;
}
.foot-note .el-icon { color: var(--navy-500); font-size: 14px; margin-top: 1px; flex-shrink: 0; }

@media (max-width: 640px) {
  .map-head { flex-direction: column; }
  .group-grid { grid-template-columns: 1fr; }
}
</style>
