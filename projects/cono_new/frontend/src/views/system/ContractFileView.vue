<template>
  <div>
    <!-- 工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增资料</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="项目编号/产品型号" clearable style="width:240px" @keyup.enter="onSearch" @clear="onSearch">
          <template #append><el-button @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 项目文件管理</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="plan_number" label="项目编号" min-width="155" show-overflow-tooltip />
        <el-table-column prop="productcategory_name" label="产品名称" min-width="140" />
        <el-table-column prop="product_model" label="型号" min-width="120" />
        <el-table-column prop="quantity" label="数量" width="70" align="center" />
        <el-table-column label="电气图" width="85" align="center">
          <template #default="{ row }">
            <el-link v-if="row.electrical_drawings" :href="fileUrl(row.electrical_drawings)" target="_blank" type="primary">点击下载</el-link>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="说明书" width="85" align="center">
          <template #default="{ row }">
            <el-link v-if="row.instruction" :href="fileUrl(row.instruction)" target="_blank" type="primary">点击下载</el-link>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="其他文件" width="85" align="center">
          <template #default="{ row }">
            <el-link v-if="row.other_file" :href="fileUrl(row.other_file)" target="_blank" type="primary">点击下载</el-link>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="机械图纸" width="85" align="center">
          <template #default="{ row }">
            <el-link v-if="row.mechanical_drawings" :href="fileUrl(row.mechanical_drawings)" target="_blank" type="primary">点击下载</el-link>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="装箱清单" width="85" align="center">
          <template #default="{ row }">
            <el-link v-if="row.packing_list" :href="fileUrl(row.packing_list)" target="_blank" type="primary">点击下载</el-link>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="150" fixed="right">
          <template #default="{ row }"><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, List, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'

const router = useRouter()
const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)
const search = ref('')

const toRelative = (v) => {
  if (!v) return ''
  return v.replace(/^https?:\/\/[^/]+/, '').replace(/^\/media\//, '').replace(/^\/+/, '')
}
const fileUrl = (path) => (path ? `/media/${toRelative(path)}` : '')
const fileName = (path) => (path ? toRelative(path).split('/').pop() : '')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: page_size.value }
    if (search.value) params.keyword = search.value
    const d = await request.get('/contract-file/', { params })
    list.value = (d.results || d).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
    total.value = d.count || list.value.length
  } finally { loading.value = false }
}

const onSearch = () => { page.value = 1; fetchList() }

const openAdd = () => { if (!requirePerm(['contract_file', 'contract_file_list'], '上传资料')) return; router.push('/contract-file/new') }
const openEdit = (row) => { if (!requirePerm(['edit_contract_file'], '编辑资料')) return; router.push(`/contract-file/edit/${row.id}`) }
const handleDelete = async (row) => {
  if (!requirePerm(['delete_contract_file'], '删除资料')) return
  try {
    await ElMessageBox.confirm('确定删除该资料吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/contract-file/${row.id}/`)
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
