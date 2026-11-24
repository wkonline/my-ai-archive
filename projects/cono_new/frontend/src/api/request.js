import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

const TOKEN_KEYS = [
  'access_token',
  'refresh_token',
  'user_info',
  'user_permissions',
  'user_menus',
  'rememberDuration',
  'token_expiry_access_token',
  'token_expiry_refresh_token',
]

function tokenStorage() {
  return localStorage.getItem('access_token') ? localStorage : sessionStorage
}

function clearTokens() {
  for (const key of TOKEN_KEYS) {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  }
}

function redirectToLogin() {
  clearTokens()
  if (window.location.pathname !== '/login') window.location.href = '/login'
}

// 并发请求同时收到 401 时只刷新一次，其余请求等待同一个 Promise
let refreshPromise = null

function refreshAccessToken() {
  if (refreshPromise) return refreshPromise
  const storage = tokenStorage()
  const refresh = storage.getItem('refresh_token')
  if (!refresh) return Promise.reject(new Error('no refresh token'))

  // 用裸 axios，避免走本文件的拦截器造成递归
  refreshPromise = axios
    .post('/api/auth/refresh/', { refresh })
    .then(({ data }) => {
      storage.setItem('access_token', data.access)
      if (data.refresh) storage.setItem('refresh_token', data.refresh)
      // access token 短于 refresh token，过期时间沿用 refresh 的
      const expiry = storage.getItem('token_expiry_refresh_token')
      if (expiry) storage.setItem('token_expiry_access_token', expiry)
      return data.access
    })
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

request.interceptors.request.use(config => {
  const token = tokenStorage().getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.url?.includes('/auth/login/')) {
    const cap = JSON.parse(localStorage.getItem('_captcha') || '{}')
    if (cap.key && config.data) {
      config.data = { ...config.data, captcha_key: cap.key }
    }
  }
  return config
})

function firstErrorMessage(data) {
  if (!data) return ''
  // 500 时后端可能返回整页 HTML，直接弹出来会把页面源码糊到用户脸上
  if (typeof data === 'string') return data.includes('<') ? '' : data
  if (data.detail) return data.detail
  // DRF 字段校验错误形如 {"key": ["..."]}，直接取第一条，避免统一显示「请求失败」
  for (const value of Object.values(data)) {
    if (Array.isArray(value) && value.length) return String(value[0])
    if (typeof value === 'string') return value
  }
  return ''
}

request.interceptors.response.use(
  response => {
    // 下载类请求需要读取 content-disposition 头，返回完整响应
    if (response.config?.rawResponse) return response
    return response.data
  },
  async error => {
    const status = error.response?.status
    const detail = firstErrorMessage(error.response?.data) || '请求失败'
    const url = error.config?.url || ''
    const isAuthEndpoint = url.includes('/auth/login/') || url.includes('/auth/refresh/')

    // access token 过期（8 小时）但 refresh token 仍有效时，静默换新并重放原请求，
    // 否则"记住登录一周/一个月"会在 8 小时后直接掉回登录页。
    if (status === 401 && !isAuthEndpoint && !error.config?._retried) {
      try {
        await refreshAccessToken()
        error.config._retried = true
        error.config.headers.Authorization =
          `Bearer ${tokenStorage().getItem('access_token')}`
        return request(error.config)
      } catch {
        redirectToLogin()
        return Promise.reject(error)
      }
    }

    if (status === 401 && !isAuthEndpoint) {
      redirectToLogin()
    }
    ElMessage.error(detail)
    return Promise.reject(error)
  }
)

export default request
