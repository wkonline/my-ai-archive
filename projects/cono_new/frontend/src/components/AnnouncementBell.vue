<template>
  <div class="ann-bell">
    <button class="bell-btn" :title="unread > 0 ? `${unread} 条未读公告` : '公告通知'" @click="openPanel">
      <el-badge :value="unread" :max="99" :hidden="unread === 0" class="bell-badge">
        <el-icon :size="19"><Bell /></el-icon>
      </el-badge>
    </button>

    <el-dialog v-model="panelVisible" title="公告通知" width="min(880px, 92vw)" class="ann-dialog" append-to-body>
      <div class="ann-toolbar">
        <span class="ann-summary">
          共 {{ items.length }} 条
          <template v-if="unread > 0">，<b class="ann-unread-count">{{ unread }}</b> 条未读</template>
          <template v-else>，已全部读完</template>
        </span>
        <el-button
          type="primary" size="small" plain
          :disabled="unread === 0 || loading"
          @click="markAll"
        >全部已读</el-button>
      </div>

      <div class="ann-scroll" v-loading="loading">
        <el-empty v-if="!loading && items.length === 0" description="暂无公告" :image-size="80" />
        <ul class="ann-list">
          <li
            v-for="item in items" :key="item.id"
            class="ann-item" :class="{ 'is-unread': !item.is_read }"
            @click="openDetail(item)"
          >
            <span class="ann-dot" :class="item.is_read ? 'dot-read' : 'dot-unread'"></span>
            <div class="ann-main">
              <div class="ann-title-row">
                <el-tag size="small" :type="item.kind === 2 ? 'warning' : 'primary'" effect="plain" class="ann-kind">
                  {{ item.kind_display }}
                </el-tag>
                <span class="ann-title">{{ item.title }}</span>
                <el-tag v-if="item.is_top" size="small" type="danger" effect="plain" class="ann-top">置顶</el-tag>
                <span v-if="item.attachments?.length" class="ann-clip" :title="`${item.attachments.length} 个附件`">
                  <el-icon><Paperclip /></el-icon>{{ item.attachments.length }}
                </span>
              </div>
              <div class="ann-meta">
                <span>{{ item.publisher_name }}</span>
                <span class="ann-sep">·</span>
                <span>{{ formatTime(item.publish_time) }}</span>
                <span class="ann-status" :class="item.is_read ? 'status-read' : 'status-unread'">
                  {{ item.is_read ? '已读' : '未读' }}
                </span>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </el-dialog>

    <el-dialog v-model="detailVisible" width="min(780px, 92vw)" append-to-body class="ann-detail-dialog">
      <template #header>
        <div v-if="detail" class="ann-detail-head">
          <h3 class="ann-detail-title">{{ detail.title }}</h3>
          <div class="ann-detail-meta">
            <el-tag size="small" :type="detail.kind === 2 ? 'warning' : 'primary'" effect="plain">
              {{ detail.kind_display }}
            </el-tag>
            <el-tag v-if="detail.is_top" size="small" type="danger" effect="plain">置顶</el-tag>
            <span class="ann-detail-by">{{ detail.publisher_name }}</span>
            <span class="ann-sep">·</span>
            <span>{{ formatTime(detail.publish_time) }}</span>
          </div>
        </div>
      </template>
      <div v-if="detail" class="ann-detail-body">
        <AnnouncementContent :content="detail.content" />
        <AnnouncementAttachmentList :items="detail.attachments || []" />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { Bell, Paperclip } from '@element-plus/icons-vue'
import request from '../api/request'
import AnnouncementContent from './AnnouncementContent.vue'
import AnnouncementAttachmentList from './AnnouncementAttachmentList.vue'

const unread = ref(0)
const items = ref([])
const loading = ref(false)
const panelVisible = ref(false)
const detailVisible = ref(false)
const detail = ref(null)
let timer = null

const formatTime = (raw) => {
  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return String(raw)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fetchUnread = async () => {
  try {
    const data = await request.get('/announcement/unread-count/')
    unread.value = data?.unread || 0
  } catch {}
}

const fetchList = async () => {
  loading.value = true
  try {
    const data = await request.get('/announcement/', { params: { page_size: 100 } })
    items.value = data?.results || data || []
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

const openPanel = async () => {
  panelVisible.value = true
  await fetchList()
}

const openDetail = async (item) => {
  detail.value = item
  detailVisible.value = true
  if (!item.is_read) {
    try {
      const data = await request.post(`/announcement/${item.id}/read/`)
      item.is_read = true
      unread.value = data?.unread ?? Math.max(unread.value - 1, 0)
    } catch {}
  }
}

const markAll = async () => {
  loading.value = true
  try {
    await request.post('/announcement/read-all/')
    items.value.forEach(i => { i.is_read = true })
    unread.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUnread()
  // 每分钟轮询一次：局域网内公告不需要实时推送，轮询足够且不占资源
  timer = setInterval(fetchUnread, 60000)
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.bell-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  cursor: pointer;
  transition: background .2s;
}
.bell-btn:hover { background: rgba(255, 255, 255, 0.2); }
.bell-badge :deep(.el-badge__content) { border: none; }

.ann-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  margin-bottom: 6px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.ann-summary { font-size: 13px; color: var(--el-text-color-secondary); }
.ann-unread-count { color: var(--el-color-danger); }

/* 列表区与详情正文共用：固定高度 + 滚动条常驻可见
   （局域网里很多人不习惯隐藏式滚动条，看不到条就以为内容没了） */
.ann-scroll {
  max-height: 52vh;
  overflow-y: scroll;
  overflow-x: hidden;
  padding-right: 4px;
}

.ann-list { list-style: none; margin: 0; padding: 0; }
.ann-item {
  display: flex;
  gap: 10px;
  padding: 12px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background .18s;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.ann-item:hover { background: var(--el-fill-color-light); }
.ann-item.is-unread { background: #f5f9ff; }
.ann-item.is-unread:hover { background: #eaf3ff; }

.ann-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 7px;
}
.dot-unread { background: var(--el-color-danger); box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.16); }
.dot-read { background: var(--el-border-color); }

.ann-main { flex: 1; min-width: 0; }
.ann-title-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.ann-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ann-item.is-unread .ann-title { font-weight: 600; }
.ann-kind, .ann-top { flex-shrink: 0; }

.ann-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 5px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.ann-sep { opacity: .5; }
.ann-status {
  margin-left: auto;
  padding: 0 7px;
  border-radius: 9px;
  font-size: 11px;
  line-height: 17px;
}
.status-unread { color: var(--el-color-danger); background: #fef0f0; }
.status-read { color: var(--el-text-color-secondary); background: var(--el-fill-color); }

.ann-detail-head { padding-right: 24px; }
.ann-detail-title {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.45;
  color: var(--el-text-color-primary);
  word-break: break-word;
}
.ann-detail-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.ann-detail-by { color: var(--el-text-color-regular); }
.ann-detail-body {
  max-height: 62vh;
  overflow-y: scroll;
  overflow-x: hidden;
  padding-right: 8px;
}

/* 附件角标：列表里一眼看出这条公告带文件 */
.ann-clip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: 9px;
  font-size: 11px;
  line-height: 17px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

/* 两个滚动容器统一滚动条外观 */
.ann-scroll::-webkit-scrollbar,
.ann-detail-body::-webkit-scrollbar { width: 8px; }
.ann-scroll::-webkit-scrollbar-track,
.ann-detail-body::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}
.ann-scroll::-webkit-scrollbar-thumb,
.ann-detail-body::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 4px;
}
.ann-scroll::-webkit-scrollbar-thumb:hover,
.ann-detail-body::-webkit-scrollbar-thumb:hover { background: var(--el-text-color-placeholder); }
.ann-scroll,
.ann-detail-body { scrollbar-width: thin; scrollbar-color: var(--el-border-color-darker) var(--el-fill-color-lighter); }
</style>
