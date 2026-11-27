<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增登记</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <span class="stat-text">本年发货总数：{{ stats.chart_total || 0 }} 台/件</span>
      </div>
    </el-card>

    <!-- 图表 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :sm="12" :md="16">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><TrendCharts /></el-icon> 本年度分月发货数量</span></template>
          <BaseChart :option="monthChartOption" height="260px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="chart-card">
          <template #header><span class="chart-title"><el-icon><Histogram /></el-icon> 本年发货汇总</span></template>
          <div class="total-box">
            <span class="total-num">{{ stats.chart_total || 0 }}</span>
            <div class="total-label">总发货数量（台/件）</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 检索 -->
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
          <el-form-item label="客户名称">
            <el-input v-model="customerName" placeholder="客户名称" clearable style="width:200px" @keyup.enter="onSearch" />
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
        <span class="card-title"><el-icon><List /></el-icon> 发货流水单</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="date" label="发货日期" width="105" align="center" />
        <el-table-column prop="contract_number" label="项目编号" min-width="155" show-overflow-tooltip />
        <el-table-column prop="productcategory" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product" label="产品型号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="70" align="center" />
        <el-table-column prop="contact_person" label="收货人" min-width="95" show-overflow-tooltip />
        <el-table-column prop="phone" label="收货人联系电话" width="130" show-overflow-tooltip />
        <el-table-column prop="address" label="收货地址" min-width="160" show-overflow-tooltip />
        <el-table-column prop="delivery_man_name" label="发货人" min-width="95" />
        <el-table-column label="操作" class-name="op-cell" width="150" fixed="right">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, Refresh, TrendCharts, Histogram, List, Edit, Delete } from '@element-plus/icons-vue'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import { download } from '../../utils/download'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const startDate = ref('')
const endDate = ref('')
const customerName = ref('')
const stats = ref({})

const monthChartOption = computed(() => {
  const colors = pickColors((stats.value.values || []).length)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'category', data: stats.value.months || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: [{
      type: 'bar',
      data: (stats.value.values || []).map((v, idx) => ({
        value: v,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 30,
    }]
  }
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (customerName.value) params.customer_name = customerName.value
    const d = await request.get('/delivery/', { params })
    list.value = (d.results || d).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = d.count || list.value.length
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await request.get('/delivery/stats/')
  } catch {}
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  startDate.value = ''
  endDate.value = ''
  customerName.value = ''
  page.value = 1
  fetchList()
}
const exportData = () => {
  const params = {}
  if (startDate.value) params.start_date = startDate.value
  if (endDate.value) params.end_date = endDate.value
  if (customerName.value) params.customer_name = customerName.value
  return download('/delivery/export/', params, 'delivery_data.xlsx')
}

const openAdd = () => { if (!requirePerm(['delivery_add'], '新增发货单')) return; router.push('/delivery/new') }
const openEdit = (row) => { if (!requirePerm(['delivery_edit'], '编辑发货单')) return; router.push(`/delivery/edit/${row.id}`) }

const handleDelete = async (row) => {
  if (!requirePerm(['delivery_delete'], '删除发货单')) return
  try {
    await ElMessageBox.confirm(`确认删除该发货记录？`, '提示', { type: 'warning' })
    await request.delete(`/delivery/${row.id}/`)
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
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stat-text { color: #4a5a6a; font-size: 13px; }
.chart-row { margin-bottom: 12px; }
.chart-card :deep(.el-card__header) { padding: 10px 14px; }
.chart-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.total-box { text-align: center; padding: 30px 0; }
.total-num { font-size: 42px; font-weight: 700; color: #0078e0; }
.total-label { font-size: 13px; color: #909399; margin-top: 6px; }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.filter-body { padding-top: 4px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
