<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑客户' : '新增客户' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><User /></el-icon> 客户信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-input v-model="form.company_name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contact_person" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.phone" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务经理">
              <el-select v-model="form.saler" filterable style="width:100%">
                <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="地址">
              <el-input v-model="form.address" type="textarea" :rows="2" placeholder="选填" />
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
import { User } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, company_name: '', contact_person: '', phone: '', address: '', saler: null })
const users = ref([])

const loadData = async () => {
  try {
    users.value = (await request.get('/user/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/customer/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, company_name: data.company_name || '', contact_person: data.contact_person || '',
      phone: data.phone || '', address: data.address || '', saler: data.saler || null,
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.company_name) { ElMessage.warning('请填写客户名称'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/customer/${form.id}/`, form)
    else await request.post('/customer/', form)
    ElMessage.success('保存成功')
    router.push('/customer')
  } finally { saving.value = false }
}

const goBack = () => router.push('/customer')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
