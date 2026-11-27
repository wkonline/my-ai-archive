80<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-count">
          <div class="stat-value">{{ stats.count }}</div>
          <div class="stat-label">合同总数</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-amount">
          <div class="stat-value">¥{{ (stats.total_amount / 10000).toFixed(1) }}万</div>
          <div class="stat-label">合同总额</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-pending">
          <div class="stat-value">{{ stats.pending_count || 0 }}</div>
          <div class="stat-label">未完结</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-done">
          <div class="stat-value">{{ stats.done_count || 0 }}</div>
          <div class="stat-label">已完结</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表展示 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :sm="24" :md="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="chart-title"><el-icon><TrendCharts /></el-icon> {{ chartYear }}年度分月合同业绩</span>
          </template>
          <BaseChart :option="monthlyChartOption" height="240px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="chart-title"><el-icon><User /></el-icon> {{ chartYear }}年度合同额前五</span>
          </template>
          <BaseChart :option="topCustomerChartOption" height="240px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="chart-title"><el-icon><PieChart /></el-icon> {{ chartYear }}年度业务员销售业绩占比</span>
          </template>
          <BaseChart :option="salesmanChartOption" height="240px" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增合同</el-button>
        <el-button class="btn-export" @click="exportContracts"><el-icon><Download /></el-icon>&nbsp;数据导出</el-button>
        <el-button class="btn-goods" @click="goContractProduct"><el-icon><Goods /></el-icon>&nbsp;合同产品展示</el-button>
        <span class="spacer"></span>
        <el-button size="small" class="btn-filter" @click="toggleFilter">{{ filterVisible ? '收起' : '筛选' }} <el-icon><ArrowDown v-if="!filterVisible" /><ArrowUp v-else /></el-icon></el-button>
      </div>
      <el-collapse-transition>
        <el-form v-show="filterVisible" inline class="search-form">
          <el-form-item label="日期范围">
            <el-date-picker v-model="searchRange" type="daterange" value-format="YYYY-MM-DD" placeholder="开始~结束" style="width:220px" @change="fetchList" />
          </el-form-item>
          <el-form-item label="状态">
            <el-radio-group v-model="searchStatus" @change="fetchList">
              <el-radio-button :value="''">全部</el-radio-button>
              <el-radio-button :value="'invoiced_debt'">已开票欠款</el-radio-button>
              <el-radio-button :value="'uninvoiced'">未开票合同</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="检索">
            <el-input v-model="searchKeyword" placeholder="请输入公司名称或合同号" clearable style="width:220px" @keyup.enter="fetchList" />
          </el-form-item>
          <el-form-item>
            <el-button @click="fetchList"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
            <el-button @click="resetSearch"><el-icon><Refresh /></el-icon>&nbsp;重置</el-button>
          </el-form-item>
        </el-form>
      </el-collapse-transition>
    </el-card>

<!-- 列表 -->
    <el-card shadow="never">
      <el-table :data="list" stripe border v-loading="loading" @sort-change="onSortChange">
        <el-table-column prop="order_number" label="序号" width="100" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" fixed show-overflow-tooltip />
        <el-table-column prop="date" label="合同日期" width="105" sortable="custom" />
        <el-table-column prop="contract_number" label="合同编号" min-width="155">
          <template #default="{ row }">
            <router-link :to="`/contract/${row.id}`" class="link-cell">{{ row.contract_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="total_price" label="合同金额" width="115" align="right">
          <template #default="{ row }">
            <span class="price">¥{{ Number(row.total_price || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="回款金额" width="110" align="right">
          <template #default="{ row }">
            <span>¥{{ Number(row.total_collection || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="开票金额" width="110" align="right">
          <template #default="{ row }">
            <span>¥{{ Number(row.total_invoice || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="回款比例" width="100" :show-overflow-tooltip="false">
          <template #default="{ row }">
            <el-progress :percentage="row.payment_ratio || 0" :stroke-width="8" :status="row.payment_completed ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column label="开票比例" width="100" :show-overflow-tooltip="false">
          <template #default="{ row }">
            <el-progress :percentage="row.invoice_ratio || 0" :stroke-width="8" :status="row.invoice_completed ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column label="尾款" width="110" align="right">
          <template #default="{ row }">
            <span style="color:#f56c6c;font-weight:600">¥{{ Number(row.outstanding_balance || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="saler_name" label="业务经理" width="90" show-overflow-tooltip />
        <el-table-column label="操作" class-name="op-cell" width="280" fixed="right" :show-overflow-tooltip="false">
          <template #default="{ row }">
            <el-button class="op-btn op-detail" size="small" @click="openDetail(row)"><el-icon><View /></el-icon>&nbsp;详情</el-button>
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
            <el-button v-if="row.attachment" class="op-btn op-download" size="small" @click="downloadAttachment(row)">
              <el-icon><Download /></el-icon>&nbsp;下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          :page-size="page_size"
          :total="total"
          layout="total, prev, pager, next, jumper"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Search, Refresh, TrendCharts, PieChart, List, View, Edit, ArrowDown, ArrowUp, Goods, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import { download } from '../../utils/download'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'

const router = useRouter()

// ===== 数据 =====
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const stats = ref({ count: 0, total_amount: 0, pending_count: 0, done_count: 0 })
// ===== 图表数据 =====
const chartYear = ref(new Date().getFullYear())
const chartData = ref({ monthly: [], top_customers: [], salesman: [] })

const monthlyChartOption = computed(() => {
  const colors = pickColors(chartData.value.monthly.length)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'category', data: chartData.value.monthly.map(i => i.month), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: [{
      type: 'bar',
      data: chartData.value.monthly.map((i, idx) => ({
        value: i.amount,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 28,
    }]
  }
})

const topCustomerChartOption = computed(() => {
  const colors = pickColors(chartData.value.top_customers.length)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: chartData.value.top_customers.map(i => i.name), axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar',
      data: chartData.value.top_customers.map((i, idx) => ({
        value: i.value,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [0, 4, 4, 0] }
      })),
      barMaxWidth: 20,
    }]
  }
})

const salesmanChartOption = computed(() => {
  const colors = pickColors(chartData.value.salesman.length)
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '43%'],
      data: chartData.value.salesman,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      color: colors,
    }]
  }
})

const searchRange = ref(null)
const searchStatus = ref('')
const searchKeyword = ref('')
const filterVisible = ref(false)
const sortField = ref('')
const sortOrder = ref('')

// ===== 方法 =====
const fetchStats = async () => {
  try {
    const data = await request.get('/contract/stats/')
    stats.value = { count: 0, total_amount: 0, pending_count: 0, done_count: 0, ...data }
  } catch {}
}

const fetchCharts = async () => {
  try {
    const data = await request.get('/contract/charts/')
    chartYear.value = data.year || new Date().getFullYear()
    chartData.value = {
      monthly: data.monthly || [],
      top_customers: data.top_customers || [],
      salesman: data.salesman || [],
    }
  } catch {}
}

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (searchRange.value?.length === 2) {
      params.start_date = searchRange.value[0]
      params.end_date = searchRange.value[1]
    }
    if (searchStatus.value) params.status = searchStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (sortField.value) params.order_by = sortField.value + (sortOrder.value === 'descending' ? '-' : '')
    const data = await request.get('/contract/', { params })
    list.value = (data.results || []).map(item => ({
      ...item,
      payment_ratio: Math.round((Number(item.total_collection) / Number(item.total_price) || 0) * 100),
      invoice_ratio: Math.round((Number(item.total_invoice) / Number(item.total_price) || 0) * 100),
    }))
    total.value = data.count || 0
  } finally { loading.value = false }
}

const resetSearch = () => {
  searchRange.value = null
  searchStatus.value = ''
  searchKeyword.value = ''
  page.value = 1
  fetchList()
}

const toggleFilter = () => { filterVisible.value = !filterVisible.value }
const onSortChange = ({ prop, order }) => {
  sortField.value = prop || ''
  sortOrder.value = order || ''
  fetchList()
}

// 跳转到独立页面
const openAdd = () => { if (!requirePerm(['contract_add', 'contract_create'], '新增合同')) return; router.push('/contract/new') }
const openEdit = (row) => { if (!requirePerm(['contract_edit'], '编辑合同')) return; router.push(`/contract/edit/${row.id}`) }
const openDetail = (row) => router.push(`/contract/${row.id}`)

const handleDelete = async (row) => {
  if (!requirePerm(['contract_delete'], '删除合同')) return
  await ElMessageBox.confirm(`确认删除合同 ${row.contract_number}？`, '提示', { type: 'warning' })
  await request.delete(`/contract/${row.id}/`)
  ElMessage.success('删除成功')
  fetchList()
  fetchStats()
}

const downloadAttachment = (row) => {
  window.open(`/media/${row.attachment}`, '_blank')
}

const goContractProduct = () => router.push('/contract-product')

const exportContracts = async () => {
  const params = {}
  if (searchRange.value?.length === 2) {
    params.start_date = searchRange.value[0]
    params.end_date = searchRange.value[1]
  }
  if (searchStatus.value) params.status = searchStatus.value
  if (searchKeyword.value) params.keyword = searchKeyword.value
  if (sortField.value) params.order_by = sortField.value + (sortOrder.value === 'descending' ? '-' : '')
  await download('/contract/export/', params, 'contract_data.xlsx')
}

onMounted(() => { fetchList(); fetchStats(); fetchCharts() })
</script>

<style scoped>
.stats-row { margin-bottom: 12px; }
.chart-row { margin-bottom: 12px; }
.chart-card :deep(.el-card__header) { padding: 10px 14px; }
.chart-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.stat-card { text-align: center; cursor: default; border-top: 3px solid transparent; transition: all .2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,120,224,0.12); }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
.stat-count { border-top-color: #0078e0; }
.stat-count .stat-value { color: #005cc5; }
.stat-amount { border-top-color: #10b981; }
.stat-amount .stat-value { color: #059669; }
.stat-pending { border-top-color: #f59e0b; }
.stat-pending .stat-value { color: #d97706; }
.stat-done { border-top-color: #10b981; }
.stat-done .stat-value { color: #10b981; }
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 10px; }
.spacer { flex: 1; }
.search-form { margin-top: 12px; }
.price { font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }

/* 工具栏按钮 */
.btn-add, .btn-import, .btn-export, .btn-goods, .btn-filter { display: inline-flex; align-items: center; font-weight: 500; }
.btn-add { background: linear-gradient(135deg, #0078e0, #004a99); border-color: #005cc5; color: #fff; }
.btn-add:hover { background: linear-gradient(135deg, #60a5fa, #005cc5); border-color: #0078e0; color: #fff; }
.btn-export { background: linear-gradient(135deg, #8b5cf6, #7c3aed); border-color: #7c3aed; color: #fff; }
.btn-export:hover { background: linear-gradient(135deg, #a78bfa, #7c3aed); border-color: #8b5cf6; color: #fff; }
.btn-goods { background: linear-gradient(135deg, #f59e0b, #d97706); border-color: #d97706; color: #fff; }
.btn-goods:hover { background: linear-gradient(135deg, #fbbf24, #d97706); border-color: #f59e0b; color: #fff; }
.btn-filter { background: #f4f6f8; border-color: #dcdfe6; color: #606266; }
.btn-filter:hover { background: #eef2f7; color: var(--text-main); }

/* 列表文字统一 12px */
:deep(.el-table) {
  font-size: 12px;
}
:deep(.el-table th.el-table__cell) {
  font-size: 12px;
  font-weight: 600;
}
:deep(.el-table td.el-table__cell) {
  font-size: 12px;
}
:deep(.el-table .cell) {
  font-size: 12px;
}
:deep(.el-table .el-progress__text) {
  font-size: 11px;
}

/* 操作列按钮：详情/编辑/下载 默认 12px */
.op-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border-radius: 6px;
  font-size: 12px !important;
  line-height: 1;
}
:deep(.op-btn .el-button__text),
:deep(.op-btn span) { font-size: 12px !important; }
.link-cell {
  color: #0078e0;
  text-decoration: none;
  &:hover { text-decoration: underline; }
}
.op-btn .el-icon { font-size: 12px !important; }
.op-btn + .op-btn { margin-left: 4px; }
.op-detail { color: #0078e0; border-color: #7cc4f7; background: #eaf5ff; }
.op-detail:hover { background: #0078e0; color: #fff; border-color: #0078e0; }
.op-edit { color: #f59e0b; border-color: #fcd34d; background: #fffbeb; }
.op-edit:hover { background: #f59e0b; color: #fff; border-color: #f59e0b; }
.op-download { color: #10b981; border-color: #6ee7b7; background: #ecfdf5; }
.op-download:hover { background: #10b981; color: #fff; border-color: #10b981; }
</style>
