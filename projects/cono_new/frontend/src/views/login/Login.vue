<template>
  <div class="login-page">
    <div class="deco-grid"></div>
    <div class="deco-circle deco-circle-1"></div>
    <div class="deco-circle deco-circle-2"></div>
    <div class="deco-line"></div>
    <div class="deco-line deco-line-2"></div>
    <div class="deco-line deco-line-3"></div>

    <div class="login-wrap">
      <div class="login-brand">
        <div class="brand-logo">
          <img src="/logo.png" alt="Logo" />
        </div>
        <h1 class="brand-title">洛阳科诺工业设备管理系统</h1>
        <p class="brand-sub">Intelligent Industrial Management Platform</p>
        <div class="brand-stats">
          <div class="stat" v-for="s in stats" :key="s.label">
            <div class="stat-num">{{ s.num }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
        <p class="brand-copy">© 2026 洛阳科诺工业智能 · 业务管理平台</p>
      </div>

      <div class="login-card" :class="{ 'register-mode': isRegister }">
        <!-- 登录模式 -->
        <template v-if="!isRegister">
          <div class="card-header">
            <span class="card-badge">新版 · 前后端分离</span>
            <h2 class="card-title">系统登录</h2>
          </div>
          <el-form :model="form" @submit.prevent>
            <el-form-item>
              <el-input v-model="form.username" placeholder="用户名" size="large" class="tech-input">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password class="tech-input" @keyup.enter="handleLogin">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
            <div class="captcha-row" v-if="showCaptcha">
              <el-form-item>
                <div class="captcha-box">
                  <el-input v-model="captchaInput" placeholder="请输入验证码" size="large" class="tech-input captcha-input" @keyup.enter="handleLogin" />
                  <img :src="captchaImage" alt="验证码" class="captcha-img" @click="fetchCaptcha" title="点击刷新" />
                </div>
              </el-form-item>
            </div>
            <div class="remember-row">
              <span class="remember-label">记住登录</span>
              <div class="remember-btns">
                <button type="button" class="rm-btn" :class="{ 'is-active': rememberDuration === 86400 }" @click="rememberDuration = 86400">当天</button>
                <button type="button" class="rm-btn" :class="{ 'is-active': rememberDuration === 604800 }" @click="rememberDuration = 604800">一周</button>
                <button type="button" class="rm-btn" :class="{ 'is-active': rememberDuration === 2592000 }" @click="rememberDuration = 2592000">一个月</button>
              </div>
            </div>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form>
          <div class="login-footer">
            <span class="footer-text">还没有账号？</span>
            <a class="footer-link" @click="switchToRegister">立即注册</a>
            <a href="http://192.168.1.202:8000/" target="_blank" class="footer-link footer-back">← 返回老版系统</a>
          </div>
        </template>

        <!-- 注册模式 -->
        <template v-else>
          <div class="card-header">
            <span class="card-badge">新用户注册</span>
            <h2 class="card-title">创建账号</h2>
          </div>
          <el-form :model="regForm" label-position="top" @submit.prevent>
            <div class="form-row">
              <el-form-item label="用户名 / 姓名 *" class="form-item">
                <el-input v-model="regForm.username" placeholder="请输入用户名（最多16字）" size="large" class="tech-input" maxlength="16">
                  <template #prefix><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
            </div>
            <div class="form-row two-col">
              <el-form-item label="手机号 *" class="form-item">
                <el-input v-model="regForm.phone" placeholder="11位手机号" size="large" class="tech-input" maxlength="11" />
              </el-form-item>
              <el-form-item label="身份证号 *" class="form-item">
                <el-input v-model="regForm.id_number" placeholder="18位身份证号" size="large" class="tech-input" maxlength="18" />
              </el-form-item>
            </div>
            <div class="form-row two-col">
              <el-form-item label="部门 *" class="form-item">
                <el-select v-model="regForm.department_id" placeholder="请选择部门" size="large" class="tech-select" style="width: 100%;">
                  <el-option v-for="d in departments" :key="d.id" :label="d.title || d.name" :value="d.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="性别" class="form-item">
                <el-select v-model="regForm.gender" size="large" class="tech-select" style="width: 100%;">
                  <el-option label="男" :value="1" />
                  <el-option label="女" :value="2" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="地址" class="form-item">
              <el-input v-model="regForm.address" placeholder="请输入联系地址" size="large" class="tech-input" />
            </el-form-item>
            <div class="form-row two-col">
              <el-form-item label="密码 *" class="form-item">
                <el-input v-model="regForm.password" type="password" placeholder="至少6位" size="large" show-password class="tech-input" />
              </el-form-item>
              <el-form-item label="确认密码 *" class="form-item">
                <el-input v-model="regForm.confirm_password" type="password" placeholder="再次输入密码" size="large" show-password class="tech-input" />
              </el-form-item>
            </div>
            <div class="captcha-row">
              <div class="captcha-box">
                <el-input v-model="regCaptchaInput" placeholder="请输入验证码" size="large" class="tech-input captcha-input" @keyup.enter="handleRegister" />
                <img :src="captchaImage" alt="验证码" class="captcha-img" @click="fetchCaptcha" title="点击刷新" />
              </div>
            </div>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleRegister">
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form>
          <div class="login-footer">
            <span class="footer-text">已有账号？</span>
            <a class="footer-link" @click="switchToLogin">立即登录</a>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores/user'
import { User, Lock } from '@element-plus/icons-vue'
import request from '../../api/request'
import { hasValidToken } from '../../utils/token'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const showCaptcha = ref(true)

// 模式切换
const isRegister = ref(false)
const switchToRegister = () => { isRegister.value = true; fetchCaptcha() }
const switchToLogin = () => { isRegister.value = false; fetchCaptcha() }

// 登录表单
const form = reactive({ username: '', password: '' })
const captchaInput = ref('')
const captchaImage = ref('')
const rememberDuration = ref(604800)

// 注册表单
const regForm = reactive({
  username: '',
  phone: '',
  id_number: '',
  department_id: null,
  gender: 1,
  address: '',
  password: '',
  confirm_password: '',
})
const regCaptchaInput = ref('')
const departments = ref([])

// 获取验证码
const fetchCaptcha = async () => {
  try {
    const res = await fetch('/api/auth/captcha/')
    const data = await res.json()
    captchaImage.value = data.image
    localStorage.setItem('_captcha', JSON.stringify({ key: data.key }))
  } catch { captchaImage.value = '' }
}

// 获取部门列表（注册用）
const fetchDepartments = async () => {
  try {
    const res = await request.get('/auth/departments/')
    const list = Array.isArray(res) ? res : (res?.results || [])
    departments.value = list
  } catch { departments.value = [] }
}

onMounted(() => {
  // 已登录用户打开登录页直接进入系统；?register=1 保留注册入口（如管理员代建账号）。
  if (route.query.register === '1') {
    isRegister.value = true
  } else if (hasValidToken()) {
    router.replace('/')
    return
  }
  fetchCaptcha()
  fetchDepartments()
})

const stats = [
  { num: '19', label: '注册用户' },
  { num: '237', label: '客户企业' },
  { num: '1882', label: '合同总数' },
  { num: '1330', label: '售后服务' },
]

// 登录
const handleLogin = async () => {
  if (!form.username || !form.password) return
  if (showCaptcha.value && !captchaInput.value) return
  loading.value = true
  try {
    const captchaKey = JSON.parse(localStorage.getItem('_captcha') || '{}')?.key || ''
    await userStore.login({
      ...form,
      captcha_key: captchaKey,
      captcha_code: captchaInput.value,
      rememberDuration: rememberDuration.value,
    })
    router.push('/')
  } catch (e) {
    if (e?.response?.status === 400) captchaInput.value = ''
    else throw e
  } finally { loading.value = false }
}

// 注册
const handleRegister = async () => {
  const f = regForm
  if (!f.username) { ElMessage.warning('请填写用户名'); return }
  if (!/^\d{11}$/.test(f.phone)) { ElMessage.warning('请填写11位手机号'); return }
  if (!/^\d{18}$/.test(f.id_number)) { ElMessage.warning('请填写18位身份证号'); return }
  if (!f.department_id) { ElMessage.warning('请选择部门'); return }
  if (!f.password) { ElMessage.warning('请填写密码'); return }
  if (f.password.length < 6) { ElMessage.warning('密码至少6位'); return }
  if (f.password !== f.confirm_password) { ElMessage.warning('两次密码不一致'); return }
  if (!regCaptchaInput.value) { ElMessage.warning('请输入验证码'); return }

  loading.value = true
  try {
    const captchaKey = JSON.parse(localStorage.getItem('_captcha') || '{}')?.key || ''
    await userStore.register({
      ...f,
      captcha_key: captchaKey,
      captcha_code: regCaptchaInput.value,
      rememberDuration: rememberDuration.value,
    })
    ElMessage.success('注册成功，正在进入系统...')
    router.push('/')
  } catch (e) {
    if (e?.response?.status === 400) regCaptchaInput.value = ''
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  height: 100vh; position: relative; overflow: hidden;
  background: linear-gradient(135deg, var(--navy-900) 0%, var(--navy-800) 40%, var(--navy-700) 100%);
}
.deco-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(0,120,224,0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,120,224,0.08) 1px, transparent 1px);
  background-size: 48px 48px;
}
.deco-circle { position: absolute; border-radius: 50%; border: 1px solid rgba(0,120,224,0.15); }
.deco-circle-1 { width: 600px; height: 600px; top: -200px; right: -150px; box-shadow: 0 0 60px rgba(0,120,224,0.15); }
.deco-circle-2 { width: 300px; height: 300px; bottom: -80px; left: -60px; box-shadow: 0 0 40px rgba(0,120,224,0.1); }
.deco-line { position: absolute; top: 0; left: 15%; width: 1px; height: 100%; background: linear-gradient(180deg, transparent, rgba(0,120,224,0.2), transparent); }
.deco-line-2 { left: 85%; background: linear-gradient(180deg, transparent, rgba(0,120,224,0.15), transparent); }
.deco-line-3 { left: 50%; background: linear-gradient(180deg, transparent, rgba(0,120,224,0.1), transparent); }

.login-wrap {
  position: relative; z-index: 2;
  display: flex; align-items: center; justify-content: center;
  gap: 80px; height: 100vh; padding: 0 60px;
}

.login-brand { color: #fff; max-width: 420px; }
.brand-logo { margin-bottom: 24px; }
.brand-logo img { height: 56px; }
.brand-title { margin: 0 0 8px; font-size: 26px; font-weight: 700; letter-spacing: 1px; text-shadow: 0 0 20px rgba(0,120,224,0.5); }
.brand-sub { margin: 0 0 40px; font-size: 11px; letter-spacing: 4px; color: rgba(255,255,255,0.7); text-transform: uppercase; }
.brand-stats { display: flex; gap: 28px; margin-bottom: 48px; }
.stat { text-align: left; }
.stat-num { font-size: 32px; font-weight: 700; color: #fff; line-height: 1; text-shadow: 0 0 20px rgba(0,120,224,0.4); }
.stat-label { font-size: 11px; color: rgba(255,255,255,0.8); margin-top: 6px; letter-spacing: 1px; }
.brand-copy { font-size: 11px; color: rgba(255,255,255,0.5); letter-spacing: 2px; }

.login-card {
  width: 380px; background: #fff;
  border-radius: 16px; padding: 40px 32px 32px;
  box-shadow: 0 20px 60px rgba(0,31,63,0.35), 0 0 0 1px rgba(255,255,255,0.5);
  transition: width .3s ease;
  max-height: 90vh; overflow-y: auto;
}
.login-card.register-mode { width: 460px; }
.card-header { text-align: center; margin-bottom: 28px; }
.card-badge {
  display: inline-block; padding: 3px 12px; border-radius: 999px;
  background: var(--navy-50); color: var(--navy-600);
  font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-bottom: 12px;
}
.card-title { margin: 0; font-size: 20px; font-weight: 700; color: var(--text-main); }

.tech-input :deep(.el-input__wrapper) {
  background: var(--navy-50) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  border-radius: 10px !important;
  transition: all .25s;
}
.tech-input :deep(.el-input__wrapper:hover),
.tech-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(0,120,224,0.4) inset !important;
  background: #fff !important;
}
.tech-input :deep(.el-input__inner) { color: var(--text-main) !important; }
.tech-input :deep(.el-input__prefix) { color: var(--navy-400) !important; }

.tech-select :deep(.el-select__wrapper) {
  background: var(--navy-50) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  border-radius: 10px !important;
  min-height: 44px !important;
}
.tech-select :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 2px rgba(0,120,224,0.4) inset !important;
  background: #fff !important;
}

.login-btn {
  width: 100%; margin-top: 8px; height: 46px;
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border: none !important; border-radius: 10px !important;
  font-size: 15px; font-weight: 600; letter-spacing: 6px;
  box-shadow: 0 4px 20px rgba(0,120,224,0.3) !important;
  transition: all .25s;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(0,120,224,0.4) !important; }

.login-footer {
  text-align: center; margin-top: 20px; font-size: 12px;
  display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
}
.footer-text { color: var(--text-dim); }
.footer-link { color: var(--navy-500); cursor: pointer; text-decoration: none; transition: color .2s; }
.footer-link:hover { color: var(--navy-700); text-decoration: underline; }
.footer-back { margin-left: 12px; color: var(--text-dim); font-size: 11px; }
.footer-back:hover { color: var(--navy-400); }

/* 验证码 */
.captcha-row { margin-bottom: 12px; }
.captcha-box { display: flex; gap: 8px; align-items: center; }
.captcha-img {
  width: 110px; height: 44px; border-radius: 8px; cursor: pointer;
  border: 1px solid var(--border); flex-shrink: 0; object-fit: contain;
  background: #fff; transition: opacity .2s;
}
.captcha-img:hover { opacity: 0.8; }
.captcha-input { flex: 1; }

/* 记住登录 */
.remember-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 4px; margin-bottom: 18px;
}
.remember-label { font-size: 13px; color: var(--text-sub); }
.remember-btns { display: flex; gap: 6px; }
.rm-btn {
  padding: 4px 14px; border-radius: 8px; font-size: 12px;
  border: 1px solid var(--border); background: var(--navy-50);
  color: var(--text-dim); cursor: pointer; transition: all .2s;
  line-height: 1.4;
}
.rm-btn:hover { border-color: var(--navy-400); color: var(--navy-600); }
.rm-btn.is-active {
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700));
  color: #fff; border-color: transparent;
  box-shadow: 0 2px 8px rgba(0,120,224,0.25);
}

/* 注册表单布局 */
.form-row { margin-bottom: 4px; }
.two-col { display: flex; gap: 12px; }
.two-col .form-item { flex: 1; min-width: 0; }
.form-item { margin-bottom: 8px; }
:deep(.el-form-item__label) {
  font-size: 12px; color: var(--text-sub);
  padding-bottom: 4px; font-weight: 500;
}

@media (max-width: 900px) {
  .login-brand { display: none; }
  .login-wrap { padding: 0 20px; gap: 0; }
  .login-card, .login-card.register-mode { width: 100%; max-width: 460px; }
}
</style>
