<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增铭牌</el-button>
        <el-button class="btn-export" @click="exportData"><el-icon><Download /></el-icon>&nbsp;数据下载</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="搜索型号..." clearable style="width:240px" @keyup.enter="onSearch">
          <template #append><el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 产品铭牌列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="productcategory_name" label="产品名称" min-width="140" />
        <el-table-column prop="product_model" label="产品型号" min-width="130" />
        <el-table-column prop="power" label="电源功率(kW)" width="105" align="center" />
        <el-table-column prop="frequency" label="电源频率(kHz)" width="105" align="center" />
        <el-table-column prop="sup_capacity" label="供电容量(kVA)" width="105" align="center" />
        <el-table-column prop="sup_voltage" label="供电电压(V)" width="100" align="center" />
        <el-table-column prop="sup_frequency" label="供电频率(Hz)" width="100" align="center" />
        <el-table-column prop="sup_current" label="供电电流(A)" width="100" align="center" />
        <el-table-column prop="max_in_temp" label="最高进水温度(°C)" width="120" align="center" />
        <el-table-column prop="max_pressure" label="最大压力(MPa)" width="105" align="center" />
        <el-table-column prop="min_flow" label="最小流量(L/min)" width="115" align="center" />
        <el-table-column prop="min_pressure" label="最小压力(MPa)" width="105" align="center" />
        <el-table-column label="操作" class-name="op-cell" width="150" fixed="right">
          <template #default="{ row }"><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination v-model:current-page="page" :page-size="50" :total="total" layout="total, prev, pager, next" @current-change="fetchList" />
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download, Search, List, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import { download } from '../../utils/download'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const search = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (search.value) params.q = search.value
    const d = await request.get('/product-label/', { params })
    list.value = (d.results || d).map((item, idx) => ({ ...item, order_number: (page.value - 1) * 50 + idx + 1 }))
    total.value = d.count || list.value.length
  } finally { loading.value = false }
}

const onSearch = () => { page.value = 1; fetchList() }
const exportData = () => {
  const params = {}
  if (search.value) params.q = search.value
  return download('/product-label/export/', params, 'product_label_data.xlsx')
}
const openAdd = () => { if (!requirePerm(['productlabel_add'], '新增产品铭牌')) return; router.push('/product-label/new') }
const openEdit = (row) => { if (!requirePerm(['productlabel_edit'], '编辑产品铭牌')) return; router.push(`/product-label/edit/${row.id}`) }
const handleDelete = async (row) => {
  if (!requirePerm(['productlabel_delete'], '删除产品铭牌')) return
  try {
    await ElMessageBox.confirm('确定删除该铭牌吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/product-label/${row.id}/`)
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
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
