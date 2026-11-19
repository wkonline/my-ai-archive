import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use(config => {
  const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage
  const token = storage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // 登录接口自动附带当前 captchaKey / captchaCode
  if (config.url?.includes('/auth/login/')) {
    const cap = JSON.parse(localStorage.getItem('_captcha') || '{}')
    if (cap.key && config.data) {
      config.data = { ...config.data, captcha_key: cap.key }
      // captcha_code 由登录页的 captchaInput 传入（不通过拦截器）
    }
  }
  return config
})

request.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || '请求失败'
    const url = error.config?.url || ''
    // 登录接口的 401 不跳转，让登录页自己提示错误
    const isLoginRequest = url.includes('/auth/login/')
    if (status === 401 && !isLoginRequest) {
      for (const key of [
        'access_token',
        'refresh_token',
        'user_info',
        'user_permissions',
        'user_menus',
        'rememberDuration',
        'token_expiry_access_token',
        'token_expiry_refresh_token',
      ]) {
        localStorage.removeItem(key)
        sessionStorage.removeItem(key)
      }
      window.location.href = '/login'
    }
    ElMessage.error(detail)
    return Promise.reject(error)
  }
)

export default request
