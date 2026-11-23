<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增客户</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="搜索客户名称或联系人..." clearable style="width:260px" @keyup.enter="onSearch">
          <template #append><el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <el-row :gutter="12" class="stats-row">
      <el-col :span="12"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.total || 0 }}</div><div class="stat-label">客户总数</div></el-card></el-col>
      <el-col :span="12"><el-card shadow="hover" class="stat-card"><div class="stat-value" style="color:#0078e0">{{ Object.keys(stats.by_saler || {}).length }}</div><div class="stat-label">业务员数</div></el-card></el-col>
    </el-row>
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 客户列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="company_name" label="客户名称" min-width="180" show-overflow-tooltip fixed />
        <el-table-column label="联系人" min-width="130">
          <template #default="{ row }">
            <span v-if="!row.contacts || !row.contacts.length" class="muted">—</span>
            <el-tooltip v-else placement="top" :show-after="200">
              <template #content>
                <div v-for="c in row.contacts" :key="c.id" class="contact-line">
                  <span class="contact-name">{{ c.name }}</span>
                  <span v-if="c.phone" class="contact-phone">{{ c.phone }}</span>
                  <span v-if="c.title" class="contact-title">{{ c.title }}</span>
                  <el-tag v-if="c.is_primary" size="small" type="success" class="contact-primary">主</el-tag>
                </div>
              </template>
              <span class="contact-summary">{{ contactSummary(row) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column prop="saler_name" label="业务经理" min-width="100" />
        <el-table-column label="操作" class-name="op-cell" width="150" fixed="right">
          <template #default="{ row }"><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination v-model:current-page="page" :page-size="50" :total="total" layout="total, prev, pager, next" @current-change="fetchList" />
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, List, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const search = ref('')
const stats = ref({})
const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (search.value) params.keyword = search.value
    const data = await request.get('/customer/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * 50 + idx + 1 }))
    total.value = data.count || list.value.length
  } finally { loading.value = false }
}

const fetchStats = async () => {
  try {
    const s2 = await request.get('/customer/stats/')
    stats.value = s2
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }

const contactSummary = (row) => {
  const contacts = row.contacts || []
  if (!contacts.length) return ''
  const primary = contacts.find(c => c.is_primary) || contacts[0]
  return contacts.length > 1 ? `${primary.name} 等 ${contacts.length} 人` : primary.name
}

const openAdd = () => router.push('/customer/new')
const openEdit = (row) => router.push(`/customer/edit/${row.id}`)
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该客户吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/customer/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList(); fetchStats()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(() => { fetchList(); fetchStats() })
</script>
<style scoped>
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stats-row { margin-bottom: 12px; }
.stat-card { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #0078e0; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.muted { color: #c0c4cc; }
.contact-summary { color: #0078e0; cursor: default; }
.contact-line { display: flex; align-items: center; gap: 8px; line-height: 22px; white-space: nowrap; }
.contact-name { font-weight: 600; }
.contact-phone { color: #c8d6e5; }
.contact-title { color: #8fa3b8; font-size: 12px; }
.contact-primary { transform: scale(0.85); }
</style>
