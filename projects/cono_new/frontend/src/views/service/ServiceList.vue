<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增登记</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <span class="stat-text">共 {{ total }} 条记录</span>
      </div>
    </el-card>

    <!-- 图表 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><TrendCharts /></el-icon> 本年度每月售后板子数量</span></template>
          <BaseChart :option="monthOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><Histogram /></el-icon> 近三年板子维修月度对比</span></template>
          <BaseChart :option="threeYearOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><PieChart /></el-icon> 本年度客户维修板子前五占比</span></template>
          <BaseChart :option="pieOption" height="220px" />
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
          <el-form-item label="日期">
            <el-date-picker v-model="searchRange" type="daterange" value-format="YYYY-MM-DD" placeholder="选择日期范围" style="width:260px" />
          </el-form-item>
          <el-form-item label="客户">
            <el-input v-model="searchCustomer" placeholder="客户名称" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="searchKeyword" placeholder="型号/产品名称" clearable style="width:200px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 售后列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip fixed />
        <el-table-column prop="productcategory_name" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_model" label="型号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="service_number" label="维修编号" min-width="130">
          <template #default="{ row }">
            <el-link type="primary" @click="openDetail(row)">{{ row.service_number }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="product_number" label="电路板编号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="warranty_display" label="质保情况" width="95" align="center" />
        <el-table-column prop="warranty_end_display" label="维修情况" width="95" align="center">
          <template #default="{ row }">
            <span :class="['status-badge', row.warranty_end_display === '正在维修' ? 'status-repairing' : 'status-normal']">{{ row.warranty_end_display }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="return_status_display" label="返件情况" width="95" align="center">
          <template #default="{ row }">
            <span :class="['status-badge', row.return_status_display === '未发货' ? 'status-not-shipped' : 'status-normal']">{{ row.return_status_display }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="接收时间" width="105" align="center" />
        <el-table-column prop="description" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" class-name="op-cell" width="200" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button><el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
            <el-button class="op-btn op-copy" size="small" @click="openCopy(row)"><el-icon><CopyDocument /></el-icon>&nbsp;复制</el-button>
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
import { Plus, Download, Search, Refresh, TrendCharts, Histogram, PieChart, List, Edit, Delete, CopyDocument } from '@element-plus/icons-vue'
import request from '../../api/request'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const searchRange = ref(null)
const searchCustomer = ref('')
const searchKeyword = ref('')

const chartData = ref({})

const monthOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
  xAxis: { type: 'category', data: chartData.value.chart_months || [], axisLabel: { fontSize: 10 } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
  series: [{
    type: 'bar',
    data: chartData.value.chart_month_values || [],
    barMaxWidth: 26,
    itemStyle: {
      color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
        { offset: 0, color: '#2dd4bf' },
        { offset: 1, color: '#14b8a6' }
      ]},
      borderRadius: [4, 4, 0, 0]
    }
  }]
}))

const threeYearOption = computed(() => {
  const years = chartData.value.chart_three_years || []
  const colors = pickColors(years.length)
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, type: 'scroll', textStyle: { fontSize: 11, overflow: 'truncate', width: 90, ellipsis: '..' }, itemWidth: 14, itemHeight: 10 },
    grid: { left: 20, right: 15, top: 28, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: chartData.value.chart_months || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: years.map((item, i) => ({
      name: String(item.year),
      type: 'bar',
      data: item.values,
      barMaxWidth: 22,
      itemStyle: { color: colors[i % colors.length], borderRadius: [4, 4, 0, 0] }
    }))
  }
})

const pieOption = computed(() => {
  const labels = chartData.value.chart_customer_labels || []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 0, type: 'scroll', orient: 'horizontal',
      textStyle: { color: '#4a5a6a', fontSize: 11 },
      itemWidth: 12, itemHeight: 8, pageIconSize: 8,
    },
    series: [{
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '43%'],
      data: labels.map((name, i) => ({
        name,
        value: (chartData.value.chart_customer_values || [])[i] || 0
      })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      color: pickColors(labels.length),
    }]
  }
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (searchRange.value?.length === 2) {
      params.start_date = searchRange.value[0]
      params.end_date = searchRange.value[1]
    }
    if (searchCustomer.value) params.customer_name = searchCustomer.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const data = await request.get('/service/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count || list.value.length
  } finally {
    loading.value = false
  }
}

const fetchCharts = async () => {
  try {
    chartData.value = await request.get('/service/charts/')
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  searchRange.value = null
  searchCustomer.value = ''
  searchKeyword.value = ''
  page.value = 1
  fetchList()
}
const exportData = () => window.open('/api/service/export/', '_blank')

const openAdd = () => router.push('/service/new')
const openEdit = (row) => router.push(`/service/edit/${row.id}`)
const openDetail = (row) => router.push(`/service/edit/${row.id}`)
const openCopy = (row) => router.push(`/service/edit/${row.id}?copy=1`)

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除该售后记录？`, '提示', { type: 'warning' })
    await request.delete(`/service/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
    fetchCharts()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchCharts()
})
</script>

<style scoped>
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stat-text { color: #4a5a6a; font-size: 13px; }
.chart-row { margin-bottom: 12px; }
.chart-card :deep(.el-card__header) { padding: 10px 14px; }
.chart-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.filter-body { padding-top: 4px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.op-copy { color: #6366f1 !important; border-color: #a5b4fc !important; background: #eaf5ff !important; }
.op-copy:hover { background: #6366f1 !important; color: #fff !important; border-color: #6366f1 !important; }
/* 表头与行样式 */
.el-table thead th { background: #f5f7fa; font-weight: 600; color: var(--text-main); font-size: 13px; }
.el-table td { font-size: 13px; }
.el-table tr:hover td { background: #f0f7ff !important; }
/* 状态列颜色更醒目 */
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.status-repairing { color: #f56c6c; border: 1px solid #f56c6c; background: #fef0f0; }
.status-not-shipped { color: #f56c6c; border: 1px solid #f56c6c; background: #fef0f0; }
.status-normal { color: #67c23a; border: 1px solid #67c23a; background: #f0f9eb; }
</style>
