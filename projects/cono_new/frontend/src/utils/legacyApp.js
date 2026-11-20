// 老版系统（前后端不分离，端口 8000）的地址。
// 默认取当前访问的主机名，避免把局域网 IP 写死在代码里；需要指向别处时设
// VITE_LEGACY_APP_URL（如本地开发时指向 http://192.168.1.202:8000/）。
const LEGACY_PORT = 8000

export const legacyAppUrl =
  import.meta.env.VITE_LEGACY_APP_URL || `${location.protocol}//${location.hostname}:${LEGACY_PORT}/`
