<template>
  <div class="page-wrap">
    <el-card shadow="never" class="form-card">
      <el-divider content-position="left"><el-icon><Lock /></el-icon> 修改密码</el-divider>
      <div class="pwd-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>请妥善保管密码，不要透露给他人。密码长度至少6位。</span>
      </div>
      <el-form :model="form" ref="formRef" :rules="rules" label-width="100px" class="pwd-form">
        <el-form-item label="当前密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <div class="footer-actions">
        <el-button @click="router.push('/user/me')">返回</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">确认修改</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, InfoFilled } from '@element-plus/icons-vue'
import request from '../../api/request'

const router = useRouter()
const formRef = ref()
const saving = ref(false)
const form = reactive({ old_password: '', new_password: '', confirm_password: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== form.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await request.post('/auth/change-password/', {
      old_password: form.old_password,
      new_password: form.new_password,
      confirm_password: form.confirm_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    setTimeout(() => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      localStorage.removeItem('user_permissions')
      localStorage.removeItem('user_menus')
      window.location.href = '/login'
    }, 800)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '修改失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-wrap { width: 100%; max-width: none; }
.form-card { width: 100%; padding: 10px 0; }
.pwd-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  margin: 0 10px 8px;
  background: #eaf5ff;
  border: 1px solid #d6ecff;
  border-radius: 6px;
  color: #0078e0;
  font-size: 13px;
}
.footer-actions {
  margin-top: 10px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
