const EXPIRY_PREFIX = 'token_expiry_'

/** 当前有效的 token 存储位置（localStorage 持久登录优先，否则 sessionStorage） */
export function activeTokenStorage() {
  return localStorage.getItem('access_token') ? localStorage : sessionStorage
}

/** 是否已登录且 token 未过期 */
export function hasValidToken() {
  const storage = activeTokenStorage()
  if (!storage.getItem('access_token')) return false
  const expiry = storage.getItem(EXPIRY_PREFIX + 'access_token')
  if (!expiry) return true
  return Date.now() < Number(expiry)
}
