<template>
  <div>
    <!-- 页头 -->
    <div class="page-head">
      <h2><el-icon><Promotion /></el-icon> 派任务单</h2>
      <div class="page-actions">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新派任务单</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
      </div>
    </div>

    <!-- 检索条件 -->
    <el-card shadow="never" class="filter-card">
      <template #header>
        <div class="filter-head">
          <span class="filter-title"><el-icon><Search /></el-icon> 检索条件</span>
          <el-link type="primary" :underline="false" @click="resetFilter"><el-icon><Refresh /></el-icon>&nbsp;清空条件</el-link>
        </div>
      </template>
      <div class="filter-body">
        <el-form inline @submit.prevent="onSearch">
          <el-form-item label="开始日期">
            <el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" style="width:160px" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" style="width:160px" />
          </el-form-item>
          <el-form-item label="项目号/合同号">
            <el-input v-model="contractNumber" placeholder="项目号或合同号" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="产品名称/型号">
            <el-input v-model="keyword" placeholder="产品名称或型号" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 统计 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :span="8"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.task_count || 0 }}</div><div class="stat-label">任务单数</div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.total_qty || 0 }}</div><div class="stat-label">下单总数量</div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" class="stat-card"><div class="stat-value" style="color:#409eff">{{ Object.keys(stats.by_manufacturer || {}).length }}</div><div class="stat-label">负责人数</div></el-card></el-col>
    </el-row>

    <!-- 分组列表 -->
    <template v-for="(group, gi) in groups" :key="gi">
      <el-card shadow="never" class="group-card">
        <template #header>
          <div class="group-head">
            <span class="group-number"><el-icon><List /></el-icon> {{ group.is_temp ? '临时计划' : group.contract_number }}</span>
            <el-tag size="small" type="info">{{ group.rows.length }} 项产品</el-tag>
          </div>
        </template>
        <el-table :data="group.rows" stripe border size="small">
          <el-table-column prop="order_number" label="序号" width="90" align="center" />
          <el-table-column prop="productcategory" label="产品名称" min-width="140" />
          <el-table-column prop="product" label="产品型号" min-width="140" />
          <el-table-column prop="plan_quantity" label="计划数量" width="90" align="center" />
          <el-table-column prop="quantity" label="下单数量" width="90" align="center" />
          <el-table-column prop="date" label="下发日期" width="110" align="center" />
          <el-table-column prop="production_man_name" label="负责人" width="100" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button><el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
    <el-empty v-if="!loading && groups.length === 0" description="暂无任务单数据" />

    <div class="pagination-row">
      <el-pagination
        v-model:current-page="page"
        :page-size="page_size"
        :total="total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, Refresh, Promotion, List, Edit, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const startDate = ref('')
const endDate = ref('')
const contractNumber = ref('')
const keyword = ref('')
const stats = ref({})

const groups = computed(() => {
  // 用 Map 保留接口返回顺序；普通对象会把数字计划 ID 键按升序重排。
  const g = new Map()
  for (const row of list.value) {
    const key = row.contract || 'default'
    if (!g.has(key)) {
      g.set(key, {
        contract_number: row.plan_number || '',
        customer: row.customer_name || '',
        is_temp: row.is_temp_plan,
        rows: []
      })
    }
    g.get(key).rows.push(row)
  }
  return [...g.values()]
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (contractNumber.value) params.contract_number = contractNumber.value
    if (keyword.value) params.keyword = keyword.value
    const d = await request.get('/task/', { params })
    list.value = (d.results || d).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = d.count || list.value.length
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await request.get('/task/stats/')
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  startDate.value = ''
  endDate.value = ''
  contractNumber.value = ''
  keyword.value = ''
  page.value = 1
  fetchList()
}
const exportData = () => window.open('/api/task/export/', '_blank')

const openAdd = () => router.push('/task/new')
const openEdit = (row) => router.push(`/task/edit/${row.id}`)

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除该任务单？`, '提示', { type: 'warning' })
    await request.delete(`/task/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchStats()
})
</script>

<style scoped>
.page-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.page-head h2 { display: inline-flex; align-items: center; gap: 8px; margin: 0; font-size: 20px; font-weight: 700; color: #17363e; }
.page-actions { display: flex; align-items: center; gap: 8px; }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.filter-body { padding-top: 4px; }
.stats-row { margin-bottom: 12px; }
.stat-card { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #0a8387; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.group-card { margin-bottom: 14px; }
.group-head { display: flex; align-items: center; justify-content: space-between; }
.group-number { display: inline-flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; color: #17363e; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
