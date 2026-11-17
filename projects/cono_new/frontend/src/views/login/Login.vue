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
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form>
        <div class="login-footer">
          <a href="http://192.168.1.202:8000/" target="_blank">← 返回老版系统</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const stats = [
  { num: '19', label: '注册用户' },
  { num: '237', label: '客户企业' },
  { num: '1882', label: '合同总数' },
  { num: '1330', label: '售后服务' },
]

const handleLogin = async () => {
  if (!form.username || !form.password) return
  loading.value = true
  try { await userStore.login(form); router.push('/') }
  finally { loading.value = false }
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
}
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

.login-btn {
  width: 100%; margin-top: 8px; height: 46px;
  background: linear-gradient(135deg, var(--navy-500), var(--navy-700)) !important;
  border: none !important; border-radius: 10px !important;
  font-size: 15px; font-weight: 600; letter-spacing: 6px;
  box-shadow: 0 4px 20px rgba(0,120,224,0.3) !important;
  transition: all .25s;
}
.login-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 28px rgba(0,120,224,0.4) !important; }

.login-footer { text-align: center; margin-top: 20px; font-size: 12px; }
.login-footer a { color: var(--text-dim); text-decoration: none; transition: color .2s; }
.login-footer a:hover { color: var(--navy-500); }

@media (max-width: 900px) { .login-brand { display: none; } }
</style>
