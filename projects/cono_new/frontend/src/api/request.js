import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
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
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    ElMessage.error(detail)
    return Promise.reject(error)
  }
)

export default request
