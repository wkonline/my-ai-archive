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
              :headers="uploadHeaders"
              :show-file-list="false"
              :data="{ contract: form.contract, field: f.field }"
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

const authStorage = localStorage.getItem('access_token') ? localStorage : sessionStorage
const uploadHeaders = { Authorization: `Bearer ${authStorage.getItem('access_token') || ''}` }
const uploadUrl = '/api/contract-file/upload/'

const fileUrl = (f) => (f && f.startsWith('/media/')) ? f : (f ? `/media/${f}` : '')
const fileName = (f) => f ? f.split('/').pop().split('\\').pop() : ''

const onUpload = (resp, field) => {
  if (resp && resp.url) form[field] = resp.url.replace(/^\/media\//, '')
}
const onUploadError = () => ElMessage.error('文件上传失败')
const removeFile = (field) => { form[field] = '' }

const loadData = async () => {
  try {
    plans.value = (await request.get('/plan/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/contract-file/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, contract: data.contract || null,
      electrical_drawings: data.electrical_drawings || '',
      instruction: data.instruction || '',
      other_file: data.other_file || '',
      mechanical_drawings: data.mechanical_drawings || '',
      packing_list: data.packing_list || '',
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.contract) { ElMessage.warning('请选择项目编号'); return }
  saving.value = true
  try {
    const payload = { ...form }
    if (form.id) await request.put(`/contract-file/${form.id}/`, payload)
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
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.file-upload-wrap { width: 100%; }
.file-upload-wrap :deep(.el-upload) { width: 100%; }
.file-upload-wrap :deep(.el-upload-dragger) { width: 100%; }
.file-info { display: flex; align-items: center; margin-top: 6px; color: #606266; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
