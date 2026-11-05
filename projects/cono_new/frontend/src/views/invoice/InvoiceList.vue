<template>
  <div>
    <!-- 批量上传 -->
    <el-card shadow="never" class="upload-card">
      <template #header>
        <span class="card-title"><el-icon><Upload /></el-icon> 批量上传（支持金蝶销售发票序时簿导出文件）</span>
      </template>
      <div class="upload-row">
        <el-upload
          :action="uploadAction"
          :headers="uploadHeaders"
          :show-file-list="false"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          accept=".xlsx,.xls"
        >
          <el-button class="btn-tech-outline"><el-icon><Upload /></el-icon>&nbsp;选择文件</el-button>
        </el-upload>
        <el-button class="btn-tech" @click="downloadTemplate">
          <el-icon><Download /></el-icon>&nbsp;模板下载
        </el-button>
      </div>
    </el-card>

    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增发票</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <span class="stat-text">共 {{ stats.count || 0 }} 条</span>
      </div>
    </el-card>

    <!-- 图表 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><TrendCharts /></el-icon> 本年度每月开票额</span></template>
          <BaseChart :option="monthChartOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><User /></el-icon> 本年度开票金额前五</span></template>
          <BaseChart :option="topCustomerChartOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><PieChart /></el-icon> 本月开票金额前五占比</span></template>
          <BaseChart :option="monthPieChartOption" height="220px" />
        </el-card>
      </el-col>
    </el-row>

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
            <el-date-picker v-model="dateFrom" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" style="width:160px" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="dateTo" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" style="width:160px" />
          </el-form-item>
          <el-form-item label="快速检索">
            <el-input v-model="keyword" placeholder="请输入客户名称或发票号" clearable style="width:280px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 发票记录 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 发票记录</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="90" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="合同号码" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="openContract(row)">{{ row.contract_number }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="开票金额" width="120" align="right">
          <template #default="{ row }"><span class="amount">¥{{ Number(row.amount || 0).toLocaleString() }}</span></template>
        </el-table-column>
        <el-table-column prop="date" label="开票日期" width="110" align="center" />
        <el-table-column prop="invoice_number" label="发票号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="invoice_man_name" label="开票人" width="100" align="center" />
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button><el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
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
import { Plus, Download, Search, Refresh, TrendCharts, PieChart, List, Edit, Delete, Upload } from '@element-plus/icons-vue'
import request from '../../api/request'
import BaseChart from '../../components/BaseChart.vue'

const router = useRouter()

const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const stats = ref({ total_amount: 0, count: 0 })

const dateFrom = ref('')
const dateTo = ref('')
const keyword = ref('')

const uploadAction = computed(() => '/api/invoice/import/')
const uploadHeaders = computed(() => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

const monthChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
  xAxis: { type: 'category', data: stats.value.monthly || [], axisLabel: { fontSize: 10 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef2f3' } } },
  series: [{
    type: 'bar',
    data: stats.value.monthly_amounts || [],
    barMaxWidth: 26,
    itemStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
        { offset: 0, color: '#14a9a3' },
        { offset: 1, color: '#0b7486' }
      ]},
      borderRadius: [4, 4, 0, 0]
    }
  }]
}))

const topCustomerChartOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: (stats.value.year_top_customers || []).map(i => i.name), axisLabel: { fontSize: 10 } },
  series: [{
    type: 'bar',
    data: (stats.value.year_top_customers || []).map(i => i.value),
    barMaxWidth: 20,
    itemStyle: { color: '#2b9ea0', borderRadius: [0, 4, 4, 0] }
  }]
}))

const monthPieChartOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, textStyle: { fontSize: 11 } },
  series: [{
    type: 'pie',
    radius: ['40%', '66%'],
    center: ['50%', '43%'],
    data: stats.value.month_top_customers || [],
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }
  }]
}))

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (keyword.value) params.keyword = keyword.value
    const data = await request.get('/invoice/', { params })
    list.value = (data.results || data).map((item, idx) => ({
      ...item,
      order_number: (page.value - 1) * page_size.value + idx + 1
    }))
    total.value = data.count || list.value.length
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await request.get('/invoice/stats/')
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  dateFrom.value = ''
  dateTo.value = ''
  keyword.value = ''
  page.value = 1
  fetchList()
}

const exportData = () => window.open('/api/invoice/export/', '_blank')
const downloadTemplate = () => window.open('/api/invoice/template/', '_blank')

const onUploadSuccess = (res) => {
  ElMessage.success(res?.detail || '上传成功')
  fetchList()
  fetchStats()
}
const onUploadError = () => ElMessage.error('上传失败，请检查文件格式')

const openAdd = () => router.push('/invoice/new')
const openEdit = (row) => router.push(`/invoice/edit/${row.id}`)
const openContract = (row) => router.push(`/contract/${row.contract}`)

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除该发票记录？`, '提示', { type: 'warning' })
    await request.delete(`/invoice/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
    fetchStats()
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
.upload-card { margin-bottom: 12px; }
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stat-text { color: #6b838a; font-size: 13px; }
.upload-row { display: flex; align-items: center; gap: 12px; }
.chart-row { margin-bottom: 12px; }
.chart-card :deep(.el-card__header) { padding: 10px 14px; }
.chart-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.filter-body { padding-top: 4px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.amount { font-weight: 600; color: #f56c6c; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
