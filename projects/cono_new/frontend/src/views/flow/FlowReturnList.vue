<template>
  <div>
    <FlowTabs />
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;返回登记</el-button>
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
          <el-form-item label="返回日期">
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
          <el-form-item>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon>&nbsp;点击搜索</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><RefreshLeft /></el-icon> 客户返回登记</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="flow_number" label="流转编号" width="170" fixed>
          <template #default="{ row }">
            <el-link type="primary" :underline="false">{{ row.flow_number }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="productcategory_name" label="产品名称" min-width="130" show-overflow-tooltip />
        <el-table-column prop="snapshot_model" label="产品型号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="snapshot_serial" label="产品序列号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客户名称" min-width="190" show-overflow-tooltip />
        <el-table-column prop="actual_return_date" label="实际返回日期" width="120" align="center" />
        <el-table-column label="是否换板" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_board_swapped ? 'warning' : 'info'" size="small">
              {{ row.is_board_swapped ? '换板' : '原板' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="new_archive_serial" label="换板后序列号" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">{{ row.new_archive_serial || '—' }}</template>
        </el-table-column>
        <el-table-column label="返回后状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.result_status === 2 ? 'danger' : 'success'" size="small">
              {{ row.result_status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="service_number" label="售后服务单" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.service_number || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="110" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>&nbsp;删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无返回记录" />
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
import { Plus, Download, Search, Refresh, RefreshLeft, Delete } from '@element-plus/icons-vue'
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
const filters = reactive({ start_date: null, end_date: null, flow_number: '', customer_name: '' })

const buildParams = () => {
  const params = { page: page.value, page_size: page_size.value }
  if (filters.start_date && filters.end_date) {
    params.start_date = filters.start_date
    params.end_date = filters.end_date
  }
  if (filters.flow_number) params.flow_number = filters.flow_number
  if (filters.customer_name) params.customer_name = filters.customer_name
  return params
}

const fetchList = async () => {
  loading.value = true
  try {
    const data = await request.get('/flow-return/', { params: buildParams() })
    const rows = data.results || data
    list.value = rows.map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count ?? rows.length
  } finally {
    loading.value = false
  }
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  Object.assign(filters, { start_date: null, end_date: null, flow_number: '', customer_name: '' })
  onSearch()
}

const exportData = () => {
  const params = buildParams()
  delete params.page
  delete params.page_size
  return download('/flow-return/export/', params, 'flow_return.xlsx')
}

const openAdd = () => { if (!requirePerm(['flow_return_add'], '返回登记')) return; router.push('/flow/return/new') }

const handleDelete = async (row) => {
  if (!requirePerm(['flow_return_delete'], '删除返回登记')) return
  try {
    await ElMessageBox.confirm(
      `确定删除「${row.flow_number}」的返回登记吗？该单会退回「在客户处」，产品档案状态同步回滚。`,
      '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/flow-return/${row.id}/`)
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
