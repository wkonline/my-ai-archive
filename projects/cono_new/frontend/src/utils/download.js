import request from '../api/request'
import { ElMessage } from 'element-plus'

function parseFilename(disposition, fallback) {
  if (!disposition) return fallback
  // 优先取 RFC 5987 的 filename*，兼容中文文件名
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposition)
  if (utf8) return decodeURIComponent(utf8[1])
  const plain = /filename="?([^";]+)"?/i.exec(disposition)
  return plain ? plain[1] : fallback
}

// 导出接口需要 Authorization 头，window.open 不会带 token 必然 401，
// 所以统一走 axios 取 blob 再触发下载。
export async function download(url, params = {}, fallbackName = 'download.xlsx') {
  let response
  try {
    response = await request.get(url, { params, responseType: 'blob', rawResponse: true })
  } catch (error) {
    // 出错时后端返回 JSON blob，读出来给出可读提示（覆盖拦截器的通用「请求失败」）
    const blob = error?.response?.data
    let shown = false
    if (blob instanceof Blob) {
      try {
        const detail = JSON.parse(await blob.text())?.detail
        if (detail) {
          ElMessage.closeAll()
          ElMessage.error(detail)
          shown = true
        }
      } catch { /* 保留拦截器的通用提示 */ }
    }
    if (!shown) ElMessage.error('下载失败')
    return
  }

  const name = parseFilename(response.headers?.['content-disposition'], fallbackName)
  const href = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = href
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(href)
}
