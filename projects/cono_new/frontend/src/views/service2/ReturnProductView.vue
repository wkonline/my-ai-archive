<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增登记</el-button>
        <el-button class="btn-import" @click="openBatchAdd"><el-icon><List /></el-icon>&nbsp;批量登记</el-button>
        <span class="spacer"></span>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="stat-text">共 {{ total }} 条记录</span>
      </div>
    </el-card>

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
          <el-form-item label="维修编号">
            <el-input v-model="serviceNumber" placeholder="维修编号" clearable style="width:180px" @keyup.enter="onSearch" />
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

    <!-- 列表 -->
    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 售后返件列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip fixed />
        <el-table-column prop="productcategory_name" label="产品名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_model" label="型号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="service_number" label="维修编号" min-width="130">
          <template #default="{ row }">
            <el-link type="primary" :underline="false">{{ row.service_number }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="发货人" min-width="95" />
        <el-table-column prop="date" label="发货时间" width="105" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }"><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && list.length === 0" description="暂无返件记录" />
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, Refresh, List, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const startDate = ref(null)
const endDate = ref(null)
const serviceNumber = ref('')
const searchCustomer = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (serviceNumber.value) params.service_number = serviceNumber.value
    if (searchCustomer.value) params.customer_name = searchCustomer.value
    const data = await request.get('/return-product/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = data.count || list.value.length
  } finally {
    loading.value = false
  }
}

const onSearch = () => { page.value = 1; fetchList() }
const resetFilter = () => {
  startDate.value = null
  endDate.value = null
  serviceNumber.value = ''
  searchCustomer.value = ''
  page.value = 1
  fetchList()
}
const exportData = () => window.open('/api/return-product/export/', '_blank')

const openAdd = () => router.push('/return-product/new')
const openEdit = (row) => router.push(`/return-product/edit/${row.id}`)
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该返件记录吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/return-product/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

const openBatchAdd = () => router.push({ path: '/return-product/new', query: { batch: '1' } })

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
.batch-hint { margin-top: 8px; color: #4a5a6a; font-size: 13px; }
</style>
