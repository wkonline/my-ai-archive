<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="搜索用户或操作内容..." clearable style="width:240px" @keyup.enter="onSearch">
          <template #append><el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 操作日志</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="55" align="center" fixed />
        <el-table-column label="日期" width="160">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="user_name" label="用户" width="110" />
        <el-table-column prop="action" label="操作内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip" label="记录IP" width="120" />
      </el-table>
      <div class="pagination-row">
        <el-pagination v-model:current-page="page" :page-size="page_size" :total="total" layout="total, prev, pager, next, jumper" @current-change="fetchList" />
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import { Download, Search, List } from '@element-plus/icons-vue'
import request from '../../api/request'

const list = ref([])
const total = ref(0)

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const search = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (search.value) params.search = search.value
    const data = await request.get('/log/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count || list.value.length
  } finally { loading.value = false }
}

const onSearch = () => { page.value = 1; fetchList() }
const exportData = () => window.open('/api/log/export/', '_blank')

onMounted(fetchList)
</script>
<style scoped>
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
