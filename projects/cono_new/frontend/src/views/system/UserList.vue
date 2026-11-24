<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;新建用户</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="搜索姓名或手机..." clearable style="width:240px" @keyup.enter="onSearch">
          <template #append><el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 用户列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column prop="username" label="姓名" min-width="110" />
        <el-table-column prop="gender_display" label="性别" width="60" align="center" />
        <el-table-column prop="id_number" label="身份证号" min-width="175" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机" width="120" />
        <el-table-column prop="department_name" label="所属部门" min-width="115" />
        <el-table-column prop="role_display" label="角色" width="100" />
        <el-table-column prop="create_date" label="入职时间" width="105" align="center" />
        <el-table-column label="操作" class-name="op-cell" width="230" fixed="right">
          <template #default="{ row }"><el-button v-if="isAdmin" class="op-btn op-perm" size="small" @click="openPermission(row)"><el-icon><Lock /></el-icon>&nbsp;权限</el-button>
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, List, Edit, Delete, Lock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)
const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const search = ref('')

const fetchList = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    if (search.value) params.search = search.value
    const data = await request.get('/user/', { params })
    list.value = (data.results || data).map((item, idx) => ({ ...item, order_number: (page.value - 1) * 50 + idx + 1 }))
    total.value = data.count || list.value.length
  } finally { loading.value = false }
}

const onSearch = () => { page.value = 1; fetchList() }
const openAdd = () => { if (!requirePerm(['user_add'], '新建用户')) return; router.push('/user/new') }
const openEdit = (row) => { if (!requirePerm(['user_edit'], '编辑用户')) return; router.push(`/user/edit/${row.id}`) }
const openPermission = (row) => { if (!requirePerm(['auth_user_permission'], '配置用户权限')) return; router.push(`/user/permission/${row.id}`) }
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该用户吗？删除后不可恢复。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/user/${row.id}/`)
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
