<template>
  <div>
    <div class="page-head">
      <h2>生产计划</h2>
      <div class="page-actions">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增计划</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
      </div>
    </div>

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
          <el-form-item label="快速检索">
            <el-input v-model="keyword" placeholder="产品名称、型号或合同号" clearable style="width:280px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
          </el-form-item>
        </el-form>
        <div class="quick-filter">
          <span class="quick-label">快捷筛选：</span>
          <el-radio-group v-model="completed" @change="onSearch">
            <el-radio-button :value="''">全部</el-radio-button>
            <el-radio-button value="False">未完工</el-radio-button>
            <el-radio-button value="True">已完结</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-card>

    <el-row :gutter="12" class="stats-row">
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value">{{ stats.total_qty || 0 }}</div><div class="stat-label">总数量</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value" style="color:#f56c6c">{{ stats.pending || 0 }}</div><div class="stat-label">待生产</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value" style="color:#e6a23c">{{ stats.in_production || 0 }}</div><div class="stat-label">生产中</div></el-card></el-col>
      <el-col :span="6"><el-card shadow="hover" class="stat-card"><div class="stat-value" style="color:#67c23a">{{ stats.completed || 0 }}</div><div class="stat-label">已完成</div></el-card></el-col>
    </el-row>

    <template v-for="(group, gi) in groups" :key="gi">
      <el-card shadow="never" class="group-card">
        <template #header>
          <div class="group-head">
            <span class="group-number"><el-icon><List /></el-icon> 项目编号：{{ group.contract_number }}</span>
            <el-tag size="small" class="btn-tech-outline">{{ group.count }} 项产品</el-tag>
          </div>
        </template>
        <el-table :data="group.rows" stripe border size="small" :span-method="spanMethod" :row-class-name="rowClassName">
          <el-table-column prop="order_number" label="序号" width="80" align="center" />
          <el-table-column prop="productcategory_name" label="产品名称" min-width="140">
            <template #default="{ row }">
              <template v-if="row._rowType === 'config'">
                <strong>配置信息：</strong>{{ row.configuration || '无' }}
              </template>
              <template v-else>{{ row.productcategory_name }}</template>
            </template>
          </el-table-column>
          <el-table-column prop="product_model" label="型号" min-width="140" />
          <el-table-column prop="quantity" label="数量" width="80" align="center" />
          <el-table-column prop="unit_display" label="单位" width="70" align="center" />
          <el-table-column prop="effective_date" label="生效日期" width="110" align="center" />
          <el-table-column prop="delivery_date" label="交货日期" width="110" align="center" />
          <el-table-column prop="production_man_name" label="制单人" width="100" />
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <template v-if="row._rowType === 'main'">
                <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button><el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <div class="pagination-row">
      <el-pagination v-model:current-page="page" :page-size="50" :total="total" layout="total, prev, pager, next" @current-change="fetchList" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Search, Refresh, TrendCharts, PieChart, List, Edit, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'
import BaseChart from '../../components/BaseChart.vue'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const startDate = ref('')
const endDate = ref('')
const contractNumber = ref('')
const keyword = ref('')
const completed = ref('')
const stats = ref({})

const groups = computed(() => {
  // 用 Map 保留接口返回顺序；普通对象会把数字合同 ID 键按升序重排，
  // 导致最新添加的计划反而排到后面。
  const g = new Map()
  for (const row of list.value) {
    const key = row.contract_reserve || row.contract || 'default'
    if (!g.has(key)) {
      let contract_number = row.contract_number || row.contract_reserve || '备用编号'
      let customer = row.customer_name || '临时备用计划'
      if (row.contract_reserve) customer = '临时备用计划'
      g.set(key, { contract_number, customer, rows: [], count: 0 })
    }
    const group = g.get(key)
    group.rows.push({ ...row, _rowType: 'main' })
    group.rows.push({ ...row, _rowType: 'config' })
    group.count++
  }
  return [...g.values()]
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ordering: '-id' }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (contractNumber.value) params.contract_number = contractNumber.value
    if (keyword.value) params.keyword = keyword.value
    if (completed.value) params.completed = completed.value
    const d = await request.get('/plan/', { params })
    const results = d.results || d
    list.value = results.map((item, idx) => ({ ...item, order_number: (page.value - 1) * 50 + idx + 1 }))
    total.value = d.count || list.value.length
  } finally { loading.value = false }
}

const fetchStats = async () => {
  try { stats.value = await request.get('/plan/stats/') } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  startDate.value = ''; endDate.value = ''; contractNumber.value = ''; keyword.value = ''; completed.value = ''
  page.value = 1; fetchList()
}
const exportData = () => window.open('/api/plan/export/', '_blank')
const openAdd = () => router.push('/plan/new')
const openEdit = (row) => router.push(`/plan/edit/${row.id}`)

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除该生产计划？`, '提示', { type: 'warning' })
    await request.delete(`/plan/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 单元格合并：每条计划两行 —— 第一行产品信息，第二行配置信息独占一整行
const spanMethod = ({ row, column }) => {
  if (row._rowType === 'config') {
    // 配置行：从「产品名称」列开始，向后合并覆盖到「操作」列（序号和操作列本身不重复占用）
    if (column.label === '产品名称') return [1, 7]   // 产品名称+型号+数量+单位+生效+交货+制单人 = 7 列
    return [0, 0]
  }
  // 主行：序号列跨两行
  if (column.label === '序号') return [2, 1]
  return [1, 1]
}
const rowClassName = ({ row }) => (row._rowType === 'config' ? 'config-row' : '')

onMounted(() => { fetchList(); fetchStats() })
</script>

<style scoped>
.page-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.page-head h2 { display: inline-flex; align-items: center; gap: 8px; margin: 0; font-size: 20px; font-weight: 700; color: #17363e; }
.page-head h2::before { content: ""; width: 4px; height: 20px; border-radius: 2px; background: linear-gradient(180deg, #19b4ad, #0b7486); }
.page-actions { display: flex; align-items: center; gap: 8px; }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.filter-body { padding-top: 4px; }
.quick-filter { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-top: 1px dashed #dce8ea; }
.quick-label { color: #6a8086; font-size: 13px; }
.stats-row { margin-bottom: 12px; }
.stat-card { text-align: center; }
.stat-value { font-size: 24px; font-weight: 700; color: #0a8387; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.group-card { margin-bottom: 14px; }
.group-head { display: flex; align-items: center; justify-content: space-between; }
.group-number { display: inline-flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; color: #17363e; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.group-card :deep(.config-row td) { background: #f9f9f9 !important; }
.group-card :deep(.config-row td .cell) { line-height: 1.6; }
.group-card :deep(.config-row strong) { color: #17363e; }
</style>
