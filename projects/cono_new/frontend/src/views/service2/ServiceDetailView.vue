<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增登记</el-button>
        <el-button class="btn-import" @click="openBatchAdd"><el-icon><List /></el-icon>&nbsp;批量登记</el-button>
        <el-button class="btn-goods" @click="openKnowledge"><el-icon><Reading /></el-icon>&nbsp;知识库搜索</el-button>
        <span class="spacer"></span>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="stat-text">共 {{ total }} 条记录</span>
      </div>
    </el-card>

    <!-- 图表 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><TrendCharts /></el-icon> 本年度每月维修板子数量</span></template>
          <BaseChart :option="monthOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><Histogram /></el-icon> 近三年板子维修数量对比</span></template>
          <BaseChart :option="threeYearOption" height="220px" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><PieChart /></el-icon> 本月维修人员数量占比</span></template>
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
          <el-form-item label="开始时间">
            <el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="开始时间" style="width:160px" />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="结束时间" style="width:160px" />
          </el-form-item>
          <el-form-item label="产品搜索">
            <el-input v-model="keyword" placeholder="产品名称或型号" clearable style="width:200px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="客户名称">
            <el-input v-model="searchCustomer" placeholder="客户名称" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;点击搜索</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 分组卡片列表 -->
    <template v-for="row in list" :key="row.id">
      <el-card shadow="never" class="record-card">
        <template #header>
          <div class="record-head">
            <span class="record-number"><el-icon><Document /></el-icon> 项目编号：<el-link type="primary" :underline="false">{{ row.service_number }}</el-link></span>
            <div><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
              <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
            </div>
          </div>
        </template>
        <el-table :data="[row]" stripe border size="small" style="table-layout:fixed;width:100%">
          <el-table-column prop="order_number" label="序号" width="60" align="center" />
          <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="productcategory_name" label="产品名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="product_model" label="产品型号" min-width="130" show-overflow-tooltip />
          <el-table-column prop="product_number" label="电路板编号" min-width="120" show-overflow-tooltip />
          <el-table-column prop="warranty_display" label="质保状态" width="95" align="center" />
          <el-table-column prop="repairman_name" label="维修工程师" min-width="115" />
          <el-table-column prop="service_date" label="接收时间" width="105" align="center" />
          <el-table-column prop="repair_date" label="维修完成时间" width="120" align="center" />
        </el-table>
        <div class="detail-row"><span class="detail-label">故障现象</span><span class="detail-value">{{ row.fault_text }}</span></div>
        <div class="detail-row"><span class="detail-label">故障原因</span><span class="detail-value">{{ row.fault_reason }}</span></div>
        <div class="detail-row"><span class="detail-label">维修方法</span><span class="detail-value">{{ row.repair_method }}</span></div>
      </el-card>
    </template>
    <el-empty v-if="!loading && list.length === 0" description="暂无维修记录" />
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
import { Plus, Download, Search, Refresh, TrendCharts, Histogram, PieChart, List, Reading, Document, Edit, Delete } from '@element-plus/icons-vue'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { download } from '../../utils/download'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const startDate = ref(null)
const endDate = ref(null)
const keyword = ref('')
const searchCustomer = ref('')

const chartData = ref({})

const monthOption = computed(() => {
  const colors = pickColors((chartData.value.chart_month_values || []).length)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'category', data: chartData.value.chart_months || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: [{
      type: 'bar',
      data: (chartData.value.chart_month_values || []).map((v, idx) => ({
        value: v,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 26,
    }]
  }
})

const threeYearOption = computed(() => {
  const years = chartData.value.chart_three_years || []
  const colors = pickColors(years.length)
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 20, right: 15, top: 28, bottom: 30, containLabel: true },
    xAxis: { type: 'category', data: chartData.value.chart_months || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: years.map((item, i) => ({
      name: String(item.year),
      type: 'line',
      smooth: true,
      data: item.values,
      itemStyle: { color: colors[i % colors.length] },
      lineStyle: { width: 3 },
      symbolSize: 6
    }))
  }
})

const pieOption = computed(() => {
  const labels = chartData.value.chart_repairman_labels || []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
      textStyle: { fontSize: 11 },
      pageIconColor: '#aaa',
      pageInactiveIconColor: '#ddd',
      pageIconSize: 12
    },
    color: pickColors(labels.length),
    series: [{
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '43%'],
      data: labels.map((name, i) => ({
        name,
        value: (chartData.value.chart_repairman_values || [])[i] || 0
      })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }
    }]
  }
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (keyword.value) params.keyword = keyword.value
    if (searchCustomer.value) params.customer_name = searchCustomer.value
    const data = await request.get('/servicedetail/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count || list.value.length
  } finally {
    loading.value = false
  }
}

const fetchCharts = async () => {
  try {
    chartData.value = await request.get('/servicedetail/charts/')
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  startDate.value = null
  endDate.value = null
  keyword.value = ''
  searchCustomer.value = ''
  page.value = 1
  fetchList()
}
const exportData = () => {
  const params = {}
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  if (keyword.value) params.keyword = keyword.value
  if (searchCustomer.value) params.customer_name = searchCustomer.value
  return download('/servicedetail/export/', params, 'servicedetail_data.xlsx')
}

const openAdd = () => router.push('/servicedetail/new')
const openEdit = (row) => router.push(`/servicedetail/edit/${row.id}`)
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该维修记录吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/servicedetail/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
const openBatchAdd = () => router.push({ path: '/servicedetail/new', query: { batch: '1' } })
const openKnowledge = () => router.push({ path: '/servicedetail/new', query: { knowledge: '1' } })

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
.record-card { margin-bottom: 12px; }
.record-card :deep(.el-card__header) { padding: 10px 14px; }
.record-head { display: flex; align-items: center; justify-content: space-between; }
.record-number { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #1a2533; }
.detail-row { display: flex; padding: 8px 14px; border-bottom: 1px solid #ebeef5; font-size: 13px; }
.detail-row:last-child { border-bottom: none; }
.detail-label { width: 100px; flex-shrink: 0; color: #909399; font-weight: 600; }
.detail-value { flex: 1; color: var(--text-main); line-height: 1.6; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.batch-hint { margin-top: 8px; color: #4a5a6a; font-size: 13px; }
.kb-search { margin-bottom: 12px; }
.kb-summary { margin-bottom: 12px; }
.kb-col-title { margin: 0 0 8px; color: #0078e0; font-size: 13px; font-weight: 700; }
.kb-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px; border-radius: 6px; background: #f4f6f9; margin-bottom: 6px; font-size: 13px; color: #1a2533; line-height: 1.5; }
.kb-case { border: 1px solid #eaf5ff; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; background: #fff; }
.kb-case-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; color: #1a2533; font-weight: 700; font-size: 13px; }
.kb-field { font-size: 13px; color: #1a2533; line-height: 1.6; margin-bottom: 5px; }
.kb-field b { color: #4a5a6a; }
.kb-meta { color: #8a97a5; font-size: 12px; }
</style>
