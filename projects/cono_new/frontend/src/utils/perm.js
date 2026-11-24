import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

// 权限码可以传数组表示「任一满足即可」，与后端 HasPermission 的 OR 语义一致
function toCodes(codes) {
  return Array.isArray(codes) ? codes : [codes]
}

export function hasPerm(codes) {
  const store = useUserStore()
  return toCodes(codes).some(code => store.hasPerm(code))
}

// 无权限时只提示并返回 false，调用方据此决定是否跳转/发请求
export function requirePerm(codes, action = '该操作') {
  if (hasPerm(codes)) return true
  ElMessage.warning(`您没有「${action}」权限，请联系管理员`)
  return false
}
