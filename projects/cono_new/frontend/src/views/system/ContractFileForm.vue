<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑资料' : '新增资料' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Folder /></el-icon> 项目文件信息</el-divider>
        <el-form-item label="项目编号" required>
          <el-select v-model="form.contract" filterable style="width:100%">
            <el-option v-for="p in plans" :key="p.id" :label="(p.contract_number || p.contract_reserve || p.id) + ' - ' + (p.product_model || '')" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-for="f in fileFields" :key="f.field" :label="f.label">
          <div class="file-upload-wrap">
            <el-upload
              :action="uploadUrl"
              :http-request="(opts) => uploadFile(opts, f.field)"
              :show-file-list="false"
              :on-success="(resp) => onUpload(resp, f.field)"
              :on-error="onUploadError"
              drag
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">点击选择或拖拽文件到此处</div>
            </el-upload>
            <div v-if="form[f.field]" class="file-info">
              <el-icon><Paperclip /></el-icon>
              <el-link :href="fileUrl(form[f.field])" target="_blank" type="primary" style="margin:0 6px">{{ fileName(form[f.field]) }}</el-link>
              <el-button link type="danger" size="small" @click="removeFile(f.field)"><el-icon><Close /></el-icon></el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Folder, UploadFilled, Paperclip, Close } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const plans = ref([])
const fileFields = [
  { field: 'electrical_drawings', label: '电气图' },
  { field: 'instruction', label: '说明书' },
  { field: 'other_file', label: '其他文件' },
  { field: 'mechanical_drawings', label: '机械图纸' },
  { field: 'packing_list', label: '装箱清单' },
]
const form = reactive({ id: null, contract: null, electrical_drawings: '', instruction: '', other_file: '', mechanical_drawings: '', packing_list: '' })

// action 走 el-upload 默认 ajax 需要完整路径；http-request 走 axios，baseURL 已是 /api
const uploadUrl = '/api/contract-file/upload/'
const uploadEndpoint = '/contract-file/upload/'

// 走 axios 而非 el-upload 自带 ajax：复用统一拦截器，access token 过期时可静默刷新后重放
const uploadFile = ({ file }, field) => {
  if (!form.contract) { ElMessage.warning('请先选择项目编号'); return Promise.reject(new Error('no contract')) }
  const fd = new FormData()
  fd.append('file', file)
  fd.append('contract', String(form.contract))
  fd.append('field', field)
  return request.post(uploadEndpoint, fd)
}

// 后端 FileField 序列化后是绝对 URL（http://host/media/xxx），统一取 path 部分
const toRelative = (v) => {
  if (!v) return ''
  return v.replace(/^https?:\/\/[^/]+/, '').replace(/^\/media\//, '').replace(/^\/+/, '')
}
const fileUrl = (f) => (f ? `/media/${toRelative(f)}` : '')
const fileName = (f) => (f ? toRelative(f).split('/').pop() : '')

// 后端 upload 返回的是 ContractFile 序列化结果，没有 url 字段，要按 field 取对应字段。
// upload 会按 contract 自动建记录，记下 id 让保存走 PATCH，避免再 POST 出一条空记录。
const onUpload = (resp, field) => {
  const value = resp && resp[field]
  if (value) {
    if (resp.id) form.id = resp.id
    form[field] = toRelative(value)
    ElMessage.success('上传成功')
  } else {
    ElMessage.error('上传失败：返回数据异常')
  }
}
// 错误提示由 request.js 响应拦截器统一弹出
const onUploadError = () => {}
const removeFile = (field) => { form[field] = '' }

const loadData = async () => {
  try {
    plans.value = (await request.get('/plan/?page_size=200', { silent: true })).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/contract-file/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, contract: data.contract || null,
      electrical_drawings: toRelative(data.electrical_drawings),
      instruction: toRelative(data.instruction),
      other_file: toRelative(data.other_file),
      mechanical_drawings: toRelative(data.mechanical_drawings),
      packing_list: toRelative(data.packing_list),
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.contract) { ElMessage.warning('请选择项目编号'); return }
  saving.value = true
  try {
    // 文件本身由 upload 接口直接落库，这里只同步项目编号和"删除"操作。
    // FileField 不接受字符串，清空必须传 null，保留则省略该字段。
    const payload = { contract: form.contract }
    for (const f of fileFields) {
      if (!form[f.field]) payload[f.field] = null
    }
    if (form.id) await request.patch(`/contract-file/${form.id}/`, payload)
    else await request.post('/contract-file/', payload)
    ElMessage.success('保存成功')
    router.push('/contract-file')
  } finally { saving.value = false }
}

const goBack = () => router.push('/contract-file')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.file-upload-wrap { width: 100%; }
.file-upload-wrap :deep(.el-upload) { width: 100%; }
.file-upload-wrap :deep(.el-upload-dragger) { width: 100%; }
.file-info { display: flex; align-items: center; margin-top: 6px; color: #606266; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
