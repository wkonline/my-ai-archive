<template>
  <div>
    <!-- 批量上传 -->
    <el-card shadow="never" class="upload-card">
      <template #header>
        <span class="card-title"><el-icon><Upload /></el-icon> 批量上传（支持金蝶销售发票序时簿导出文件）</span>
      </template>
      <div class="upload-area" @dragover.prevent="dragOver=true" @dragleave="dragOver=false" @drop.prevent="onDrop" @click="fileInputRef.click()">
        <input ref="fileInputRef" type="file" accept=".xlsx,.xls" style="display:none" @change="onFileChange" />
        <div class="upload-content" :class="{ 'is-dragover': dragOver }">
          <el-icon class="upload-icon" :size="48"><Upload /></el-icon>
          <p class="upload-text">将文件拖拽到此处，或<span class="upload-link">点击选择</span></p>
          <p class="upload-hint">支持 .xlsx / .xls 格式（金蝶销售发票序时簿导出文件）</p>
          <p v-if="previewFileName" class="upload-filename">✅ {{ previewFileName }}</p>
        </div>
      </div>
      <div class="upload-actions" v-if="previewRows.length > 0">
        <el-button type="primary" :loading="importLoading" @click="confirmImport" size="large">
          <el-icon><Upload /></el-icon>&nbsp;上 传（共 {{ previewRows.length }} 条）
        </el-button>
        <el-button @click="clearPreview" :disabled="importLoading">取消</el-button>

      </div>
    </el-card>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewDialogVisible" title="发票数据预览" width="950px" destroy-on-close>
      <div v-if="previewLoading" style="text-align:center;padding:30px">
        <el-icon :size="32" class="is-loading"><Loading /></el-icon>
        <p style="margin-top:12px;color:#909399">正在解析文件...</p>
      </div>
      <div v-else-if="previewError" style="padding:20px">
        <el-alert :title="previewError" type="error" :closable="false" />
      </div>
      <div v-else-if="previewRows.length === 0" style="padding:20px;text-align:center;color:#909399">
        <el-empty description="文件中没有找到有效数据" :image-size="80" />
      </div>
      <template v-else>
        <el-alert
          v-if="previewHasError"
          :title="'⚠️ 检测到 ' + previewErrorCount + ' 条数据存在错误，请先修正后再上传'"
          type="warning"
          :closable="false"
          style="margin-bottom:12px"
        />
        <el-alert
          v-else
          :title="'✅ 数据校验通过，共 ' + previewRows.length + ' 条，可点击下方「上传」按钮完成导入'"
          type="success"
          :closable="false"
          style="margin-bottom:12px"
        />
        <el-table :data="previewRows" border size="small" max-height="400" style="font-size:12px">
          <el-table-column prop="row_no" label="行号" width="60" align="center" />
          <el-table-column prop="contract_number" label="订单单号" min-width="120" show-overflow-tooltip />
          <el-table-column prop="invoice_number" label="发票号码" min-width="120" show-overflow-tooltip />
          <el-table-column prop="customer_name" label="购货单位" min-width="160" show-overflow-tooltip />
          <el-table-column prop="amount" label="开票金额" width="100" align="right">
            <template #default="{ row }">¥{{ Number(row.amount || 0).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column prop="date" label="开票日期" width="110" align="center" />
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.errors.length === 0" type="success" size="small">正常</el-tag>
              <el-tag v-else type="danger" size="small">错误</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="错误信息" min-width="220">
            <template #default="{ row }">
              <span v-if="row.errors.length === 0" style="color:#67c23a;font-size:11px">✓ 无错误</span>
              <span v-else style="color:#f56c6c;font-size:11px">{{ row.errors.join('；') }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-dialog>

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
        <el-table-column prop="order_number" label="序号" width="55" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="合同号码" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <el-button type="primary" link @click="openContract(row)">{{ row.contract_number }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="开票金额" width="105" align="right">
          <template #default="{ row }"><span class="amount">¥{{ Number(row.amount || 0).toLocaleString() }}</span></template>
        </el-table-column>
        <el-table-column prop="date" label="开票日期" width="100" align="center" />
        <el-table-column prop="invoice_number" label="发票号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="invoice_man_name" label="开票人" width="85" align="center" />
        <el-table-column label="操作" width="160" fixed="right">
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
import { Plus, Download, Search, Refresh, TrendCharts, PieChart, List, Edit, Delete, Upload, Check, Loading } from '@element-plus/icons-vue'
import request from '../../api/request'
import BaseChart from '../../components/BaseChart.vue'
import { pickColors } from '../../components/chartColors'

const router = useRouter()
const fileInputRef = ref(null)

const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const stats = ref({ total_amount: 0, count: 0 })

const dateFrom = ref('')
const dateTo = ref('')
const keyword = ref('')

// 上传相关
const dragOver = ref(false)
const previewRows = ref([])
const previewLoading = ref(false)
const previewError = ref('')
const previewHasError = ref(false)
const previewSkipped = ref(0)
const previewFileName = ref('')
const previewDialogVisible = ref(false)
const importLoading = ref(false)
const currentFile = ref(null)

const previewErrorCount = computed(() => previewRows.value.filter(r => r.errors.length > 0).length)

const readFilePreview = async (file) => {
  currentFile.value = file
  previewFileName.value = file.name
  previewLoading.value = true
  previewError.value = ''
  previewRows.value = []
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await request.post('/invoice/preview/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    previewRows.value = res.rows || []
    previewHasError.value = res.has_error || false
    previewSkipped.value = res.skipped || 0
    previewDialogVisible.value = true
  } catch (e) {
    previewError.value = e?.response?.data?.detail || '文件解析失败，请检查格式'
    previewDialogVisible.value = true
  } finally {
    previewLoading.value = false
  }
}

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) readFilePreview(file)
  e.target.value = ''
}

const onDrop = (e) => {
  dragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) readFilePreview(file)
}

const confirmImport = async () => {
  if (!previewRows.value.length) { ElMessage.warning('没有数据可导入'); return }
  if (previewHasError.value) { ElMessage.warning('存在错误数据，请先修正后再上传'); return }
  importLoading.value = true
  try {
    if (!currentFile.value) { ElMessage.warning('请先选择文件'); importLoading.value = false; return }
    const formData = new FormData()
    formData.append('file', currentFile.value)
    const res = await request.post('/invoice/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success(res?.detail || '导入成功')
    previewDialogVisible.value = false
    previewRows.value = []
    previewFileName.value = ''
    fetchList()
    fetchStats()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '导入失败')
  } finally {
    importLoading.value = false
  }
}

const clearPreview = () => {
  previewRows.value = []
  previewFileName.value = ''
  currentFile.value = null
  previewDialogVisible.value = false
  if (fileInputRef.value) fileInputRef.value.value = ''
}

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

const topCustomerChartOption = computed(() => {
  const colors = pickColors((stats.value.year_top_customers || []).length)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 20, right: 15, top: 28, bottom: 20, containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: (stats.value.year_top_customers || []).map(i => i.name), axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar',
      data: (stats.value.year_top_customers || []).map((i, idx) => ({
        value: i.value,
        itemStyle: { color: colors[idx % colors.length], borderRadius: [0, 4, 4, 0] }
      })),
      barMaxWidth: 20,
    }]
  }
})

const monthPieChartOption = computed(() => {
  const data = stats.value.month_top_customers || []
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
      data: data.map((item) => ({ name: item.name, value: item.value })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      color: pickColors(data.length),
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
.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all .2s;
}
.upload-area:hover { border-color: #0078e0; background: #f5f7fa; }
.is-dragover { border-color: #0078e0; background: #eaf5ff; }
.upload-content { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.upload-icon { color: #c0c4cc; }
.upload-text { color: #606266; font-size: 14px; margin: 0; }
.upload-link { color: #0078e0; cursor: pointer; font-weight: 600; }
.upload-hint { color: #909399; font-size: 12px; margin: 0; }
.upload-filename { color: #67c23a; font-size: 13px; font-weight: 600; margin: 0; }
.upload-actions { margin-top: 12px; display: flex; gap: 8px; justify-content: center; }
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stat-text { color: #4a5a6a; font-size: 13px; }
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
