<template>
  <div>
    <FlowTabs />
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;寄给客户</el-button>
        <span class="spacer"></span>
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
          <el-form-item label="寄出日期">
            <el-date-picker v-model="filters.start_date" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width:150px" />
            <span class="date-sep">至</span>
            <el-date-picker v-model="filters.end_date" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width:150px" />
          </el-form-item>
          <el-form-item label="流转编号">
            <el-input v-model="filters.flow_number" placeholder="流转编号" clearable style="width:190px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="客户名称">
            <el-input v-model="filters.customer_name" placeholder="客户名称" clearable style="width:180px" @keyup.enter="onSearch" />
          </el-form-item>
          <el-form-item label="流转状态">
            <el-select v-model="filters.status" placeholder="全部" clearable style="width:140px">
              <el-option label="在客户处" :value="1" />
              <el-option label="已返回" :value="2" />
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
        <span class="card-title"><el-icon><Van /></el-icon> 寄给客户登记</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="flow_number" label="流转编号" width="170" fixed>
          <template #default="{ row }">
            <el-link type="primary" :underline="false">{{ row.flow_number }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="productcategory_name" label="产品名称" min-width="110" show-overflow-tooltip />
        <el-table-column prop="product_model" label="产品型号" min-width="110" show-overflow-tooltip />
        <el-table-column prop="archive_serial" label="产品序列号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="express_number" label="快递单号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="contact_name" label="联系人" width="90" />
        <el-table-column prop="ship_date" label="寄出日期" width="105" align="center" />
        <el-table-column prop="situation" label="情况描述" min-width="160" show-overflow-tooltip />
        <el-table-column label="流转状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'warning' : 'success'" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 1" class="op-btn op-edit" size="small" @click="openEdit(row)">
              <el-icon><Edit /></el-icon>&nbsp;编辑
            </el-button>
            <el-button v-if="row.status === 1" class="op-btn op-delete" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>&nbsp;删除
            </el-button>
            <el-button v-if="row.status === 1" class="op-btn" size="small" type="success" @click="openReturn(row)">
              <el-icon><RefreshLeft /></el-icon>&nbsp;返回登记
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无寄出记录" />
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, Refresh, Van, Edit, Delete, RefreshLeft } from '@element-plus/icons-vue'
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
const filters = reactive({
  start_date: null, end_date: null, flow_number: '', customer_name: '', status: null,
})

const buildParams = () => {
  const params = { page: page.value, page_size: page_size.value }
  if (filters.start_date && filters.end_date) {
    params.start_date = filters.start_date
    params.end_date = filters.end_date
  }
  if (filters.flow_number) params.flow_number = filters.flow_number
  if (filters.customer_name) params.customer_name = filters.customer_name
  if (filters.status) params.status = filters.status
  return params
}

const fetchList = async () => {
  loading.value = true
  try {
    const data = await request.get('/flow-out/', { params: buildParams() })
    const rows = data.results || data
    list.value = rows.map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count ?? rows.length
  } finally {
    loading.value = false
  }
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  Object.assign(filters, { start_date: null, end_date: null, flow_number: '', customer_name: '', status: null })
  onSearch()
}

const exportData = () => {
  const params = buildParams()
  delete params.page
  delete params.page_size
  return download('/flow-out/export/', params, 'flow_out.xlsx')
}

const openAdd = () => { if (!requirePerm(['flow_out_add'], '寄给客户登记')) return; router.push('/flow/out/new') }
const openEdit = (row) => { if (!requirePerm(['flow_out_edit'], '编辑寄出登记')) return; router.push(`/flow/out/edit/${row.id}`) }
const openReturn = (row) => { if (!requirePerm(['flow_return_add'], '客户返回登记')) return; router.push({ path: '/flow/return/new', query: { flow_out: row.id } }) }

const handleDelete = async (row) => {
  if (!requirePerm(['flow_out_delete'], '删除寄出登记')) return
  try {
    await ElMessageBox.confirm(
      `确定删除寄出单「${row.flow_number}」吗？删除后该产品档案会退回公司库存。`,
      '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/flow-out/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
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
.date-sep { margin: 0 6px; color: #8a96a3; }
</style>
