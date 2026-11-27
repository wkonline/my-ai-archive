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
          <img src="/logo-white.png" alt="科诺" />
        </div>
        <h1 class="brand-title">洛阳科诺工业设备管理系统</h1>
        <p class="brand-sub">Intelligent Industrial Management Platform</p>
        <div class="brand-slogan">
          <img src="/brand-slogan.png" alt="科诺，让世界感知中国温度" />
        </div>
        <p class="brand-copy">© 2026 洛阳科诺工业智能 · 业务管理平台</p>
      </div>

      <div class="login-card">
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
          <a :href="legacyAppUrl" target="_blank" class="footer-link footer-back">← 返回老版系统</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { hasValidToken } from '../../utils/token'
import { legacyAppUrl } from '../../utils/legacyApp'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const showCaptcha = ref(true)

// 登录表单
const form = reactive({ username: '', password: '' })
const captchaInput = ref('')
const captchaImage = ref('')
const rememberDuration = ref(604800)

// 获取验证码
const fetchCaptcha = async () => {
  try {
    const res = await fetch('/api/auth/captcha/')
    const data = await res.json()
    captchaImage.value = data.image
    localStorage.setItem('_captcha', JSON.stringify({ key: data.key }))
  } catch { captchaImage.value = '' }
}

onMounted(() => {
  // 已登录用户打开登录页直接进入系统
  if (hasValidToken()) {
    router.replace('/')
    return
  }
  fetchCaptcha()
})

// 登录
const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  if (showCaptcha.value && !captchaInput.value) {
    ElMessage.warning('请输入验证码')
    return
  }
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
    // 错误提示由 axios 拦截器统一弹出，这里不重复提示。
    // 验证码一次性使用：无论因何失败都要换新图，否则用户会反复提交同一个失效验证码
    captchaInput.value = ''
    await fetchCaptcha()
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
.brand-logo img {
  height: 64px; width: auto;
  filter: drop-shadow(0 0 24px rgba(120,190,255,0.55));
}
.brand-title { margin: 0 0 8px; font-size: 26px; font-weight: 700; letter-spacing: 1px; text-shadow: 0 0 20px rgba(0,120,224,0.5); }
.brand-sub { margin: 0 0 36px; font-size: 11px; letter-spacing: 4px; color: rgba(255,255,255,0.7); text-transform: uppercase; }
/* 书法标语：单行不换行，图片本身已旋转 8° 倾斜。
   旋转后外接框 619x130（宽高比 4.76）。限宽 400px 让倾斜的右端
   留出视觉余量，不与品牌区右边界顶死 */
.brand-slogan { margin-bottom: 40px; }
.brand-slogan img {
  display: block; width: 400px; max-width: 100%; height: auto;
  filter: drop-shadow(0 0 18px rgba(0,120,224,0.45));
}
.brand-copy { font-size: 11px; color: rgba(255,255,255,0.5); letter-spacing: 2px; }

.login-card {
  width: 392px; background: #fff;
  border-radius: var(--radius-xl); padding: 42px 34px 34px;
  box-shadow: 0 1px 3px rgba(15,40,70,0.10), 0 24px 64px rgba(0,31,63,0.22);
  transition: width .3s var(--ease);
  max-height: 90vh; overflow-y: auto;
}
.card-header { text-align: center; margin-bottom: 28px; }
.card-badge {
  display: inline-block; padding: 3px 12px; border-radius: 999px;
  background: var(--navy-50); color: var(--navy-600);
  font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-bottom: 12px;
}
.card-title { margin: 0; font-size: 20px; font-weight: 700; color: var(--text-main); }

.tech-input :deep(.el-input__wrapper) {
  background: var(--bg-subtle) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  border-radius: var(--radius-md) !important;
  transition: all var(--dur) var(--ease);
}
.tech-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--border-bright) inset !important;
  background: #fff !important;
}
.tech-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--navy-400) inset, 0 0 0 3px rgba(0,120,224,0.12) !important;
  background: #fff !important;
}
.tech-input :deep(.el-input__inner) { color: var(--text-main) !important; }
.tech-input :deep(.el-input__prefix) { color: var(--navy-400) !important; }

.tech-select :deep(.el-select__wrapper) {
  background: var(--navy-50) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  border-radius: var(--radius-md) !important;
  min-height: 44px !important;
}
.tech-select :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 2px rgba(0,120,224,0.4) inset !important;
  background: #fff !important;
}

.login-btn {
  width: 100%; margin-top: 8px; height: 46px;
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border: none !important; border-radius: var(--radius-md) !important;
  font-size: 15px; font-weight: 600; letter-spacing: 6px;
  box-shadow: 0 4px 20px rgba(0,120,224,0.3) !important;
  transition: all .25s;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(0,120,224,0.4) !important; }

.login-footer {
  text-align: center; margin-top: 20px; font-size: 12px;
  display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
}
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

@media (max-width: 900px) {
  /* 窄屏不再整体隐藏品牌区：书法标语是品牌核心内容，需保留；
     只收起系统名与英文副标题，避免挤占登录卡片的垂直空间 */
  .login-wrap { flex-direction: column; padding: 24px 20px; gap: 20px; justify-content: center; }
  .login-brand { display: block; max-width: 100%; text-align: center; }
  .brand-logo { display: none; }
  .brand-title, .brand-sub, .brand-copy { display: none; }
  .brand-slogan { margin-bottom: 0; }
  .brand-slogan img { width: 260px; margin: 0 auto; }
  .login-card { width: 100%; max-width: 460px; }
}
</style>
