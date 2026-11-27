<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd"><el-icon><Plus /></el-icon>&nbsp;发布公告</el-button>
        <span class="spacer"></span>
        <el-input v-model="search" placeholder="搜索标题..." clearable style="width:240px" @keyup.enter="onSearch">
          <template #append><el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button></template>
        </el-input>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="card-title"><el-icon><Bell /></el-icon> 公告通知列表</span>
      </template>
      <el-table :data="list" stripe border v-loading="loading">
        <el-table-column prop="order_number" label="序号" width="60" align="center" fixed />
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.kind === 2 ? 'warning' : 'primary'" effect="plain">
              {{ row.kind_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="220">
          <template #default="{ row }">
            <el-tag v-if="row.is_top" size="small" type="danger" effect="plain" class="top-tag">置顶</el-tag>
            <span>{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_active ? 'success' : 'info'" effect="plain">
              {{ row.is_active ? '已发布' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publisher_name" label="发布人" width="110" />
        <el-table-column label="发布时间" width="150">
          <template #default="{ row }">{{ formatTime(row.publish_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="230" fixed="right">
          <template #default="{ row }">
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
            <el-button class="op-btn" size="small" @click="toggleActive(row)">
              {{ row.is_active ? '下架' : '发布' }}
            </el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination v-model:current-page="page" :page-size="50" :total="total" layout="total, prev, pager, next" @current-change="fetchList" />
      </div>
    </el-card>

    <el-dialog v-model="formVisible" :title="form.id ? '编辑公告' : '发布公告'" width="620px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="128" show-word-limit placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="类型" prop="kind">
          <el-radio-group v-model="form.kind">
            <el-radio :value="1">公告</el-radio>
            <el-radio :value="2">通知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="form.is_top" />
          <span class="form-hint">置顶后始终排在列表最前</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="发布" inactive-text="下架" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" maxlength="5000" show-word-limit placeholder="请输入公告内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Bell, Edit, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'

const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const formVisible = ref(false)
const formRef = ref(null)

const emptyForm = () => ({ id: null, title: '', content: '', kind: 1, is_top: false, is_active: true })
const form = reactive(emptyForm())
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

const formatTime = (raw) => {
  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return String(raw)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const fetchList = async () => {
  loading.value = true
  try {
    // 管理页要看到已下架的公告，include_inactive 由后端按权限放行
    const params = { page: page.value, include_inactive: 1 }
    if (search.value) params.search = search.value
    const data = await request.get('/announcement/', { params })
    const rows = data.results || data
    list.value = rows.map((item, idx) => ({ ...item, order_number: (page.value - 1) * 50 + idx + 1 }))
    total.value = data.count || rows.length
  } finally { loading.value = false }
}

const onSearch = () => { page.value = 1; fetchList() }

const openAdd = () => {
  if (!requirePerm(['announcement_add'], '发布公告')) return
  Object.assign(form, emptyForm())
  formVisible.value = true
}

const openEdit = (row) => {
  if (!requirePerm(['announcement_edit'], '编辑公告')) return
  Object.assign(form, {
    id: row.id, title: row.title, content: row.content,
    kind: row.kind, is_top: row.is_top, is_active: row.is_active,
  })
  formVisible.value = true
}

const submitForm = async () => {
  const ok = await formRef.value?.validate().catch(() => false)
  if (!ok) return
  saving.value = true
  try {
    const payload = {
      title: form.title, content: form.content, kind: form.kind,
      is_top: form.is_top, is_active: form.is_active,
    }
    if (form.id) await request.put(`/announcement/${form.id}/`, payload)
    else await request.post('/announcement/', payload)
    ElMessage.success(form.id ? '已保存' : '发布成功')
    formVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row) => {
  if (!requirePerm(['announcement_edit'], '修改公告状态')) return
  try {
    await request.patch(`/announcement/${row.id}/`, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已下架' : '已发布')
    fetchList()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (row) => {
  if (!requirePerm(['announcement_delete'], '删除公告')) return
  try {
    await ElMessageBox.confirm('确定删除该公告吗？所有人的已读记录会一并删除。', '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await request.delete(`/announcement/${row.id}/`)
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
.top-tag { margin-right: 6px; }
.form-hint { margin-left: 10px; font-size: 12px; color: var(--el-text-color-secondary); }
</style>
