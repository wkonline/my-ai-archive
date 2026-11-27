<template>
  <div class="ann-manage">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-button class="btn-add" @click="openAdd">
          <el-icon><Plus /></el-icon>&nbsp;发布公告
        </el-button>
        <span class="spacer"></span>
        <el-input
          v-model="search" placeholder="搜索标题..." clearable style="width:240px"
          @keyup.enter="onSearch" @clear="onSearch"
        >
          <template #append>
            <el-button type="primary" @click="onSearch"><el-icon><Search /></el-icon></el-button>
          </template>
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
        <el-table-column label="附件" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.attachments?.length" class="attach-badge">
              <el-icon><Paperclip /></el-icon>{{ row.attachments.length }}
            </span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
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
            <el-button class="op-btn op-edit" size="small" @click="openEdit(row)">
              <el-icon><Edit /></el-icon>&nbsp;编辑
            </el-button>
            <el-button class="op-btn" size="small" @click="toggleActive(row)">
              {{ row.is_active ? '下架' : '发布' }}
            </el-button>
            <el-button class="op-btn op-delete" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>&nbsp;删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page" :page-size="50" :total="total"
          layout="total, prev, pager, next" @current-change="fetchList"
        />
      </div>
    </el-card>

    <el-dialog v-model="formVisible" :title="form.id ? '编辑公告' : '发布公告'" width="720px" top="6vh">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="128" show-word-limit placeholder="请输入公告标题" />
        </el-form-item>
        <div class="form-row">
          <el-form-item label="类型" prop="kind">
            <el-radio-group v-model="form.kind">
              <el-radio :value="1">公告</el-radio>
              <el-radio :value="2">通知</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="置顶">
            <el-switch v-model="form.is_top" />
          </el-form-item>
          <el-form-item label="状态">
            <el-switch v-model="form.is_active" active-text="发布" inactive-text="下架" />
          </el-form-item>
        </div>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content" type="textarea" :rows="9" maxlength="5000" show-word-limit
            placeholder="请输入公告内容"
          />
          <div class="form-hint">正文里的 http 链接会自动变成可点击的超链接。</div>
        </el-form-item>

        <el-form-item label="附件">
          <div class="attach-editor">
            <el-upload
              :show-file-list="false"
              :http-request="uploadAttachment"
              :before-upload="beforeUpload"
              :disabled="uploading"
              multiple
            >
              <el-button :loading="uploading" :icon="UploadFilled">
                {{ uploading ? '上传中...' : '上传附件' }}
              </el-button>
            </el-upload>
            <span class="form-hint">单个文件不超过 50MB，上传后自动插入下载链接到正文末尾。</span>
          </div>

          <ul v-if="existingAttachments.length" class="draft-list">
            <li v-for="att in existingAttachments" :key="`e-${att.id}`" class="draft-item is-existing">
              <el-icon class="draft-icon"><Document /></el-icon>
              <span class="draft-name" :title="att.name">{{ att.name }}</span>
              <span class="draft-size">{{ formatSize(att.size) }}</span>
              <el-tag size="small" type="info" effect="plain">已发布</el-tag>
              <el-button link type="primary" size="small" @click="insertLink(att)">插入链接</el-button>
            </li>
          </ul>

          <ul v-if="draftAttachments.length" class="draft-list">
            <li v-for="att in draftAttachments" :key="att.id" class="draft-item">
              <el-icon class="draft-icon"><Document /></el-icon>
              <span class="draft-name" :title="att.name">{{ att.name }}</span>
              <span class="draft-size">{{ formatSize(att.size) }}</span>
              <el-button link type="primary" size="small" @click="insertLink(att)">插入链接</el-button>
              <el-button link type="danger" size="small" @click="removeAttachment(att)">移除</el-button>
            </li>
          </ul>
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
import {
  Plus, Search, Bell, Edit, Delete, Paperclip, Document, UploadFilled,
} from '@element-plus/icons-vue'
import request from '../../api/request'
import { requirePerm } from '../../utils/perm'

const list = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const search = ref('')
const formVisible = ref(false)
const formRef = ref(null)
// 本次编辑会话里新上传的附件；公告已有的附件由后端随公告返回
const draftAttachments = ref([])
// 公告上已发布的附件，编辑时只读展示（可重复插入链接，但不能在这里删）
const existingAttachments = ref([])

const emptyForm = () => ({ id: null, title: '', content: '', kind: 1, is_top: false, is_active: true })
const form = reactive(emptyForm())
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

const MAX_SIZE = 50 * 1024 * 1024

const formatTime = (raw) => {
  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return String(raw)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const formatSize = (bytes) => {
  const n = Number(bytes) || 0
  if (n <= 0) return ''
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
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
  draftAttachments.value = []
  existingAttachments.value = []
  formVisible.value = true
}

const openEdit = (row) => {
  if (!requirePerm(['announcement_edit'], '编辑公告')) return
  Object.assign(form, {
    id: row.id, title: row.title, content: row.content,
    kind: row.kind, is_top: row.is_top, is_active: row.is_active,
  })
  draftAttachments.value = []
  existingAttachments.value = row.attachments || []
  formVisible.value = true
}

const beforeUpload = (file) => {
  if (file.size > MAX_SIZE) {
    ElMessage.error(`${file.name} 超过 50MB，无法上传`)
    return false
  }
  return true
}

const uploadAttachment = async ({ file }) => {
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const att = await request.post('/announcement/upload-attachment/', fd)
    draftAttachments.value.push(att)
    insertLink(att)
    ElMessage.success(`${att.name} 已上传`)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 插入到正文末尾并独占一行：正文用 pre-wrap 渲染，紧跟在文字后面会被连成一段
const insertLink = (att) => {
  const line = `${att.name}：${att.download_url}`
  const current = form.content || ''
  if (current.includes(att.download_url)) return
  form.content = current && !current.endsWith('\n') ? `${current}\n${line}` : `${current}${line}`
  if (formRef.value) formRef.value.validateField('content').catch(() => {})
}

const removeAttachment = async (att) => {
  try {
    await request.delete(`/announcement/attachment/${att.token}/`)
  } catch (e) {
    // 已随公告发布的附件后端不允许删，此时只从正文里去掉链接
    if (e?.response?.status !== 400) {
      ElMessage.error(e?.response?.data?.detail || '移除失败')
      return
    }
  }
  draftAttachments.value = draftAttachments.value.filter(a => a.id !== att.id)
  form.content = (form.content || '').split('\n').filter(l => !l.includes(att.download_url)).join('\n')
}

const submitForm = async () => {
  const ok = await formRef.value?.validate().catch(() => false)
  if (!ok) return
  saving.value = true
  try {
    const payload = {
      title: form.title, content: form.content, kind: form.kind,
      is_top: form.is_top, is_active: form.is_active,
      // 显式带上本次上传的附件，正文里没插链接也不会丢
      attachment_tokens: draftAttachments.value.map(a => a.token),
    }
    if (form.id) await request.put(`/announcement/${form.id}/`, payload)
    else await request.post('/announcement/', payload)
    ElMessage.success(form.id ? '已保存' : '发布成功')
    formVisible.value = false
    draftAttachments.value = []
    existingAttachments.value = []
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
    await ElMessageBox.confirm(
      '确定删除该公告吗？所有人的已读记录和附件会一并删除。',
      '删除确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
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
.ann-manage :deep(.toolbar-card) { margin-bottom: 12px; }
.toolbar-row { display: flex; align-items: center; gap: 8px; }
.spacer { flex: 1; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: var(--text-main); }
.pagination-row { margin-top: 12px; display: flex; justify-content: flex-end; }
.top-tag { margin-right: 6px; }
.text-muted { color: var(--el-text-color-placeholder); }
.attach-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.form-row { display: flex; flex-wrap: wrap; gap: 0 18px; }
.form-hint { font-size: 12px; line-height: 1.6; color: var(--el-text-color-secondary); }

.attach-editor { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.draft-list { list-style: none; margin: 10px 0 0; padding: 0; width: 100%; }
.draft-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}
.draft-item + .draft-item { margin-top: 6px; }
.draft-item.is-existing { background: var(--el-color-primary-light-9); }
.draft-icon { color: var(--el-color-primary); flex-shrink: 0; }
.draft-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.draft-size { font-size: 12px; color: var(--el-text-color-secondary); flex-shrink: 0; }
</style>
