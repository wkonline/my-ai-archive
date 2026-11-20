<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑部门' : '新增部门' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><OfficeBuilding /></el-icon> 部门信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="部门名称" required>
              <el-input v-model="form.title" placeholder="请输入部门名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门描述">
              <el-input v-model="form.description" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>
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
import { OfficeBuilding } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, title: '', description: '' })

const loadData = async () => {
  if (!isEdit.value) return
  try {
    const data = await request.get(`/department/${route.params.id}/`)
    Object.assign(form, { id: data.id, title: data.title || '', description: data.description || '' })
  } catch {}
}

const handleSave = async () => {
  if (!form.title) { ElMessage.warning('请填写部门名称'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/department/${form.id}/`, form)
    else await request.post('/department/', form)
    ElMessage.success('保存成功')
    router.push('/department')
  } finally { saving.value = false }
}

const goBack = () => router.push('/department')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
