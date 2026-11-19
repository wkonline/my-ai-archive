import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister } from '../api/auth'

const EXPIRY_KEY_PREFIX = 'token_expiry_'
const TOKEN_KEYS = ['access_token', 'refresh_token', 'user_info', 'user_permissions', 'user_menus']

// 按 rememberDuration（秒）选择 sessionStorage（会话）或 localStorage+过期时间（持久）
function saveTokens(data, rememberDuration, expiresAt) {
  removeTokens()
  if (rememberDuration > 0) {
    for (const k of TOKEN_KEYS) localStorage.setItem(k, data[k])
    const fallbackExpiry = rememberDuration === 86400
      ? new Date(new Date().setHours(23, 59, 59, 999)).getTime()
      : Date.now() + rememberDuration * 1000
    const expiry = String(expiresAt || data.expires_at || fallbackExpiry)
    localStorage.setItem(EXPIRY_KEY_PREFIX + 'access_token', expiry)
    localStorage.setItem(EXPIRY_KEY_PREFIX + 'refresh_token', expiry)
    localStorage.setItem('rememberDuration', String(rememberDuration))
  } else {
    for (const k of TOKEN_KEYS) sessionStorage.setItem(k, data[k])
  }
}

function removeTokens() {
  for (const k of [...TOKEN_KEYS, ...TOKEN_KEYS.map(x => EXPIRY_KEY_PREFIX + x), 'rememberDuration']) {
    localStorage.removeItem(k)
    sessionStorage.removeItem(k)
  }
}

// 检查 token 是否已过期
function isTokenExpired() {
  const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage
  const expiry = storage.getItem(EXPIRY_KEY_PREFIX + 'access_token')
  if (!expiry) return false
  return Date.now() >= Number(expiry)
}

function readJson(storage, key, fallback) {
  try {
    return JSON.parse(storage.getItem(key) || JSON.stringify(fallback))
  } catch {
    return fallback
  }
}

function storedAuthState() {
  const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage
  return {
    token: storage.getItem('access_token') || '',
    user: readJson(storage, 'user_info', null),
    permissions: readJson(storage, 'user_permissions', []),
    menus: readJson(storage, 'user_menus', []),
    rememberDuration: parseInt(storage.getItem('rememberDuration') || '0', 10),
  }
}

export const useUserStore = defineStore('user', {
  state: () => {
    // 页面刷新时从 local/sessionStorage 恢复状态；已过期则自动清除
    if (isTokenExpired()) {
      for (const k of [...TOKEN_KEYS, ...TOKEN_KEYS.map(x => EXPIRY_KEY_PREFIX + x), 'rememberDuration']) {
        localStorage.removeItem(k)
        sessionStorage.removeItem(k)
      }
      return { token: '', user: null, permissions: [], menus: [], rememberDuration: 0 }
    }
    return storedAuthState()
  },
  getters: {
    isAdmin: (state) => (state.user?.role || '') === 'admin',
    hasPerm: (state) => (code) => {
      if ((state.user?.role || '') === 'admin') return true
      return (state.permissions || []).includes(code)
    },
  },
  actions: {
    async login(payload) {
      const data = await apiLogin(payload)
      const rememberDuration = payload.rememberDuration || 0
      const expiresAt = data.expires_at
      this.rememberDuration = rememberDuration
      this.token = data.access
      this.user = data.user
      this.permissions = data.user?.permissions || []
      this.menus = data.user?.menus || []
      saveTokens({
        access_token: data.access,
        refresh_token: data.refresh,
        user_info: JSON.stringify(data.user),
        user_permissions: JSON.stringify(this.permissions),
        user_menus: JSON.stringify(this.menus),
      }, rememberDuration, expiresAt)
      return data
    },
    async register(payload) {
      const data = await apiRegister(payload)
      const rememberDuration = payload.rememberDuration || 0
      this.rememberDuration = rememberDuration
      this.token = data.access
      this.user = data.user
      this.permissions = data.user?.permissions || []
      this.menus = data.user?.menus || []
      saveTokens({
        access_token: data.access,
        refresh_token: data.refresh,
        user_info: JSON.stringify(data.user),
        user_permissions: JSON.stringify(this.permissions),
        user_menus: JSON.stringify(this.menus),
      }, rememberDuration, data.expires_at)
      return data
    },
    logout() {
      this.token = ''
      this.user = null
      this.permissions = []
      this.menus = []
      removeTokens()
    },
  },
})
