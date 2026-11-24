<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑用户' : '新建用户' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><UserFilled /></el-icon> 用户信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="姓名" required>
              <el-input v-model="form.username" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select v-model="form.gender" style="width:100%">
                <el-option :value="1" label="男" />
                <el-option :value="2" label="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号" required>
              <el-input v-model="form.id_number" placeholder="请输入身份证号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机" required>
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入职时间" required>
              <el-date-picker v-model="form.create_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属部门" required>
              <el-select v-model="form.department" filterable style="width:100%">
                <el-option v-for="d in departments" :key="d.id" :label="d.title" :value="d.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属角色" required>
              <el-select v-model="form.role" :disabled="!isAdmin" style="width:100%">
                <el-option v-for="r in roles" :key="r.key" :label="`${r.name}（${r.key}）`" :value="r.key" />
              </el-select>
              <div v-if="!isAdmin" class="form-tip">只有管理员可以调整角色</div>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="!form.id">
            <el-form-item label="密码" required>
              <el-input v-model="form.password" type="password" show-password placeholder="请输入初始密码" />
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
import { UserFilled } from '@element-plus/icons-vue'
import request from '../../api/request'
import { useUserStore } from '../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin)
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, username: '', password: '', gender: 1, id_number: '', phone: '', address: '', department: null, role: 'upkeeper', create_date: '' })
const departments = ref([])
const roles = ref([])

const loadData = async () => {
  try {
    departments.value = (await request.get('/department/?page_size=200')).results || []
  } catch {}
  try {
    const data = await request.get('/auth-role/?page_size=200')
    roles.value = data.results || data || []
  } catch {}
  if (!isEdit.value) {
    // 默认角色与后端 default_role_key() 一致：内置的 upkeeper（售后服务）
    Object.assign(form, { id: null, username: '', password: '', gender: 1, id_number: '', phone: '', address: '', department: null, role: 'upkeeper', create_date: '' })
    return
  }
  try {
    const data = await request.get(`/user/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, username: data.username || '', password: '',
      gender: data.gender ?? 1, id_number: data.id_number || '', phone: data.phone || '',
      address: data.address || '', department: data.department || null,
      role: data.role || 'upkeeper', create_date: data.create_date || '',
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.username) { ElMessage.warning('请填写姓名'); return }
  if (!form.id_number) { ElMessage.warning('请填写身份证号'); return }
  if (!form.phone) { ElMessage.warning('请填写手机'); return }
  if (!form.department) { ElMessage.warning('请选择所属部门'); return }
  if (!form.create_date) { ElMessage.warning('请选择入职时间'); return }
  if (!form.id && !form.password) { ElMessage.warning('请设置密码'); return }
  saving.value = true
  try {
    if (form.id) {
      const payload = { ...form }
      delete payload.password
      await request.put(`/user/${form.id}/`, payload)
    } else {
      await request.post('/user/', form)
    }
    ElMessage.success('保存成功')
    router.push('/user')
  } finally { saving.value = false }
}

const goBack = () => router.push('/user')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.form-tip { font-size: 12px; color: #909399; line-height: 1.4; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
