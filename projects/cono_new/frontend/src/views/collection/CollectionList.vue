<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增回款</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <span class="stat-text">总金额：¥{{ Number(stats.total_amount || 0).toLocaleString() }} &nbsp;|&nbsp; 条目数：{{ stats.count || 0 }}</span>
      </div>
    </el-card>

    <!-- 图表 -->
    <el-row :gutter="12" class="chart-row">
      <el-col :xs="24" :sm="12" :md="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="chart-title"><el-icon><TrendCharts /></el-icon> 本年度月回款额</span>
          </template>
          <BaseChart :option="monthChartOption" height="240px" />
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <span class="chart-title"><el-icon><PieChart /></el-icon> 本季度业务员回款占比</span>
          </template>
          <BaseChart :option="salesmanChartOption" height="240px" />
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
            <el-input v-model="keyword" placeholder="请输入客户名称或合同号" clearable style="width:280px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 回款记录 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 回款记录</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" width="280" show-overflow-tooltip />
        <el-table-column label="合同号码" width="135" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link class="link-text" :to="`/contract/${row.contract}`">{{ row.contract_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column label="合同金额" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.contract_total_price || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="欠款余额" width="110" align="right">
          <template #default="{ row }">
            <span :style="{ color: Number(row.contract_balance || 0) > 0 ? '#f56c6c' : '#67c23a' }">
              ¥{{ Number(row.contract_balance || 0).toLocaleString() }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="回款日期" width="105" align="center" />
        <el-table-column label="回款金额" width="110" align="right">
          <template #default="{ row }">
            <span class="amount">¥{{ Number(row.amount || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="回款比例" width="105" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }">
            <el-progress :percentage="Math.round((Number(row.amount) / (Number(row.contract_total_price) || 1)) * 100)" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column prop="collection_method_display" label="回款方式" width="105" align="center" />
        <el-table-column label="总回款比例" width="110" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }">
            <el-progress :percentage="row.collection_ratio || 0" :stroke-width="8" :status="row.collection_ratio >= 100 ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column prop="saler_name" label="业务经理" width="100" show-overflow-tooltip />
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Search, Refresh, TrendCharts, PieChart, List, Edit, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import { download } from '../../utils/download'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'

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

const collectionMethods = { 1: '电汇', 2: '银承', 3: '现金', 4: '万纳信', 5: '迪链' }

const monthChartOption = computed(() => {
  const colors = pickColors((stats.value.monthly_amounts || []).length)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'category', data: stats.value.monthly || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#eef3f8' } } },
    series: [{
      type: 'bar',
      data: (stats.value.monthly_amounts || []).map((v, idx) => ({
        value: v,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 26,
    }]
  }
})

const salesmanChartOption = computed(() => {
  const data = stats.value.quarter_salesman || []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '43%'],
      data,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      color: pickColors(data.length),
      label: { show: true, fontSize: 11, formatter: '{b}: {d}%' },
    }]
  }
})

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (keyword.value) params.keyword = keyword.value
    const data = await request.get('/collection/', { params })
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
    stats.value = await request.get('/collection/stats/')
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

const exportData = () => {
  const params = {}
  if (dateFrom.value) params.date_from = dateFrom.value
  if (dateTo.value) params.date_to = dateTo.value
  if (keyword.value) params.keyword = keyword.value
  return download('/collection/export/', params, 'collection_data.xlsx')
}
const openAdd = () => { if (!requirePerm(['collection_add'], '新增回款')) return; router.push('/collection/new') }
const openEdit = (row) => { if (!requirePerm(['collection_edit'], '编辑回款')) return; router.push(`/collection/edit/${row.id}`) }

const handleDelete = async (row) => {
  if (!requirePerm(['collection_delete'], '删除回款')) return
  try {
    await ElMessageBox.confirm(`确认删除该回款记录？`, '提示', { type: 'warning' })
    await request.delete(`/collection/${row.id}/`)
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
.amount { font-weight: 600; color: #f56c6c; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
