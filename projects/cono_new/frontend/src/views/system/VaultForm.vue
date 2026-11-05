<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑账号密码' : '新增账号密码' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Key /></el-icon> 账号信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类">
              <el-input v-model="form.category" placeholder="选填，如：银行、邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="平台名称" required>
              <el-input v-model="form.name" placeholder="请输入平台名称" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="网址">
              <el-input v-model="form.url" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="登录账号">
              <el-input v-model="form.account" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="登录密码">
              <el-input v-model="form.password" type="password" show-password placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填" />
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
import { Key } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, category: '', name: '', url: '', account: '', password: '', remark: '' })

const loadData = async () => {
  if (!isEdit.value) return
  try {
    const data = await request.get(`/account-vault/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, category: data.category || '', name: data.name || '',
      url: data.url || '', account: data.account || '',
      password: data.password || '', remark: data.remark || '',
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.name) { ElMessage.warning('请填写平台名称'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/account-vault/${form.id}/`, form)
    else await request.post('/account-vault/', form)
    ElMessage.success('保存成功')
    router.push('/account-vault')
  } finally { saving.value = false }
}

const goBack = () => router.push('/account-vault')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
