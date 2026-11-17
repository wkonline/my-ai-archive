<template>
  <div class="page-wrap">
    <el-card shadow="never" class="form-card">
      <el-divider content-position="left"><el-icon><Edit /></el-icon> 修改个人资料</el-divider>
      <el-form :model="form" ref="formRef" :rules="rules" label-width="110px" class="profile-form">
        <el-form-item label="用户名">
          <el-input v-model="form.username" readonly />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio value="1">男</el-radio>
            <el-radio value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="手机" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" maxlength="11" show-word-limit />
        </el-form-item>
        <el-form-item label="身份证号" prop="id_number">
          <el-input v-model="form.id_number" placeholder="请输入身份证号" maxlength="18" show-word-limit />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入地址" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-select v-model="form.department" placeholder="请选择部门" class="full-width">
            <el-option
              v-for="dept in departments" :key="dept.id"
              :label="dept.title" :value="dept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <div class="footer-actions">
        <el-button @click="router.push('/user/me')">返回</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'
import request from '../../api/request'

const router = useRouter()

const formRef = ref()
const saving = ref(false)
const departments = ref([])
const form = reactive({
  username: '',
  gender: '',
  phone: '',
  id_number: '',
  address: '',
  department: '',
})

const rules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  id_number: [{ required: true, message: '请输入身份证号', trigger: 'blur' }],
  address: [{ required: true, message: '请输入地址', trigger: 'blur' }],
  department: [{ required: true, message: '请选择部门', trigger: 'change' }],
}

const fetchData = async () => {
  const [me, depts] = await Promise.all([
    request.get('/user/me').catch(() => null),
    request.get('/department/', { params: { page_size: 100 } }).catch(() => []),
  ])
  departments.value = depts?.results || depts || []
  if (me) {
    form.username = me.username || ''
    form.gender = me.gender ? String(me.gender) : ''
    form.phone = me.phone || ''
    form.id_number = me.id_number || ''
    form.address = me.address || ''
    form.department = me.department ? String(me.department) : ''
    if (!form.department) {
      const dept = departments.value.find(d => d.title === me.department_name)
      if (dept) form.department = String(dept.id)
    }
  }
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await request.post('/user/profile/', {
      phone: form.phone,
      id_number: form.id_number,
      address: form.address,
      gender: Number(form.gender) || undefined,
      department: Number(form.department) || undefined,
    })
    ElMessage.success('个人资料修改成功')
    const fresh = await request.get('/user/me')
    if (fresh) localStorage.setItem('user_info', JSON.stringify(fresh))
    router.push('/user/me')
  } catch (e) {
    const err = e?.response?.data
    if (err && typeof err === 'object' && !err.detail) {
      ElMessage.error(Object.values(err).flat().join('、') || '修改失败')
    } else {
      ElMessage.error(err?.detail || '修改失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.page-wrap { width: 100%; max-width: none; }
.form-card { width: 100%; padding: 10px 0; }
.full-width { width: 100%; }
.footer-actions {
  margin-top: 10px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
