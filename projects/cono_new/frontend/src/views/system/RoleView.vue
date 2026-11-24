<template>
  <div>
    <el-card shadow="never" class="toolbar">
      <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新增角色</el-button>
    </el-card>

    <el-card shadow="never">
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="key" label="角色标识" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.builtin" type="info" size="small">{{ row.key }}（内置）</el-tag>
            <span v-else>{{ row.key }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="角色名称" min-width="130" />
        <el-table-column label="权限数" width="85">
          <template #default="{ row }">{{ (row.permissions||[]).length }}</template>
        </el-table-column>
        <el-table-column label="菜单数" width="85">
          <template #default="{ row }">{{ (row.menus||[]).length }}</template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="150" fixed="right">
          <template #default="{ row }"><el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button v-if="!row.builtin" class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
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
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'

const router = useRouter()

const list = ref([])
const total = ref(0)
const page = ref(1)
const page_size = ref(50)
const loading = ref(false)

function fetchList() {
  loading.value = true
  request.get('/auth-role/', { params: { page: page.value, page_size: page_size.value } })
    .then(d => {
      list.value = (d.results || d).map((item, idx) => ({ ...item, order_number: (page.value - 1) * page_size.value + idx + 1 }))
      total.value = d.count || list.value.length
    })
    .finally(() => { loading.value = false })
}

const openAdd = () => { if (!requirePerm(['auth_role_add'], '新增角色')) return; router.push('/auth/role/new') }
const openEdit = (row) => { if (!requirePerm(['auth_role_edit'], '编辑角色')) return; router.push(`/auth/role/edit/${row.id}`) }
const handleDelete = async (row) => {
  if (!requirePerm(['auth_role_delete'], '删除角色')) return
  try {
    await ElMessageBox.confirm('确定删除该角色吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/auth-role/${row.id}/`)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.toolbar { margin-bottom: 12px; }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
