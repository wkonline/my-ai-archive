<template>
  <div>
    <FlowTabs />
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增档案</el-button>
        <span class="spacer"></span>
        <el-checkbox v-model="includeInactive" @change="onSearch">显示已停用</el-checkbox>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="stat-text">共 {{ total }} 条记录</span>
      </div>
    </el-card>

    <el-card shadow="never" class="filter-card">
      <template #header>
        <div class="filter-head">
          <span class="filter-title"><el-icon><Search /></el-icon> 检索条件</span>
          <el-link type="primary" :underline="false" @click="resetFilter"><el-icon><Refresh /></el-icon>&nbsp;清空条件</el-link>
        </div>
      </template>
      <div class="filter-body">
        <el-form inline @submit.prevent="onSearch">
          <el-form-item label="产品序列号">
            <el-input v-model="filters.serial_number" placeholder="产品序列号" clearable style="width:200px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="产品型号">
            <el-input v-model="filters.product_model" placeholder="产品型号" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="客户名称">
            <el-input v-model="filters.customer_name" placeholder="客户名称" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="当前状态">
            <el-select v-model="filters.status" placeholder="全部" clearable style="width:150px">
              <el-option label="公司库存" :value="1" />
              <el-option label="客户试用中" :value="2" />
              <el-option label="维修中" :value="3" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;点击搜索</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><Box /></el-icon> 产品档案列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading" :row-class-name="rowClass">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="productcategory_name" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_model" label="产品型号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="serial_number" label="产品序列号" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="openDetail(row)">{{ row.serial_number }}</el-link>
            <el-tag v-if="row.is_superseded" size="small" type="info" class="tag-inline">已换板</el-tag>
            <el-tag v-if="!row.is_active" size="small" type="danger" class="tag-inline">已停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler_name" label="经手人" width="100" />
        <el-table-column prop="stock_date" label="入库日期" width="110" align="center" />
        <el-table-column label="当前状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="所在位置" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.customer_name ? `客户：${row.customer_name}` : row.location_type_display }}
          </template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="230" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button v-if="row.status === 3" class="op-btn op-success" size="small" @click="markStocked(row)">
              <el-icon><CircleCheck /></el-icon>&nbsp;维修完成
            </el-button>
            <el-button class="op-btn" size="small" @click="toggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无产品档案" />
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

    <el-dialog v-model="detailVisible" title="档案流转历史" width="820px">
      <div v-if="detailRow" class="detail-head">
        <span class="detail-serial">{{ detailRow.serial_number }}</span>
        <span class="detail-meta">{{ detailRow.productcategory_name }} / {{ detailRow.product_model }}</span>
        <el-tag :type="statusType(detailRow.status)" size="small">{{ detailRow.status_display }}</el-tag>
      </div>
      <el-divider content-position="left">状态变更</el-divider>
      <el-table :data="logs" size="small" border>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="operator_name" label="操作人" width="110" />
        <el-table-column prop="remark" label="说明" min-width="220" show-overflow-tooltip />
      </el-table>
      <el-divider content-position="left">序列号转换</el-divider>
      <el-table :data="transitions" size="small" border>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="old_serial" label="旧序列号" min-width="160" />
        <el-table-column prop="new_serial" label="新序列号" min-width="160" />
        <el-table-column prop="operator_name" label="操作人" width="110" />
      </el-table>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, Refresh, Box, Edit, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import FlowTabs from './FlowTabs.vue'
import { download } from '../../utils/download'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const includeInactive = ref(false)
const filters = reactive({ serial_number: '', product_model: '', customer_name: '', status: null })

const detailVisible = ref(false)
const detailRow = ref(null)
const logs = ref([])
const transitions = ref([])

const statusType = (s) => ({ 1: 'success', 2: 'warning', 3: 'danger' }[s] || 'info')
// 已换板/已停用的档案置灰：不再参与寄出，但历史必须保留可见
const rowClass = ({ row }) => (row.is_superseded || !row.is_active ? 'row-muted' : '')

const buildParams = () => {
  const params = { page: page.value, page_size: page_size.value }
  if (filters.serial_number) params.serial_number = filters.serial_number
  if (filters.product_model) params.product_model = filters.product_model
  if (filters.customer_name) params.customer_name = filters.customer_name
  if (filters.status) params.status = filters.status
  if (includeInactive.value) params.include_inactive = 1
  return params
}

const fetchList = async () => {
  loading.value = true
  try {
    const data = await request.get('/flow-archive/', { params: buildParams() })
    const rows = data.results || data
    list.value = rows.map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count ?? rows.length
  } finally {
    loading.value = false
  }
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  Object.assign(filters, { serial_number: '', product_model: '', customer_name: '', status: null })
  includeInactive.value = false
  onSearch()
}

const exportData = () => {
  const params = buildParams()
  delete params.page
  delete params.page_size
  return download('/flow-archive/export/', params, 'product_archive.xlsx')
}

const openAdd = () => { if (!requirePerm(['flow_archive_add'], '新增档案')) return; router.push('/flow/archive/new') }
const openEdit = (row) => { if (!requirePerm(['flow_archive_edit'], '编辑档案')) return; router.push(`/flow/archive/edit/${row.id}`) }

const openDetail = async (row) => {
  detailRow.value = row
  detailVisible.value = true
  logs.value = []
  transitions.value = []
  try {
    const [logRows, transRows] = await Promise.all([
      request.get(`/flow-archive/${row.id}/logs/`),
      request.get(`/flow-archive/${row.id}/transitions/`),
    ])
    logs.value = logRows.results || logRows
    transitions.value = transRows.results || transRows
  } catch { /* 无历史不影响查看 */ }
}

const markStocked = async (row) => {
  if (!requirePerm(['flow_archive_stock'], '维修完成')) return
  try {
    await ElMessageBox.confirm(
      `确认「${row.serial_number}」维修完成并回到公司库存吗？`, '维修完成',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.post(`/flow-archive/${row.id}/stock/`)
    ElMessage.success('已标记维修完成')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

const toggleActive = async (row) => {
  if (!requirePerm(['flow_archive_edit'], '停用/启用档案')) return
  try {
    await request.post(`/flow-archive/${row.id}/toggle-active/`)
    ElMessage.success(row.is_active ? '已停用' : '已启用')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.toolbar-card { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.stat-text { color: #4a5a6a; font-size: 13px; }
.filter-card { margin-bottom: 12px; }
.filter-head { display: flex; align-items: center; justify-content: space-between; }
.filter-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.filter-body { padding-top: 4px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.tag-inline { margin-left: 6px; }
.detail-head { display: flex; align-items: center; gap: 12px; }
.detail-serial { font-size: 16px; font-weight: 700; color: var(--text-main); }
.detail-meta { color: #4a5a6a; font-size: 13px; }
</style>
