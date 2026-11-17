// 全站统一图表调色板（NAURA 深海军蓝主调 + 稳重辅助色）
export const CHART_COLORS = [
  '#0078e0', // 主蓝
  '#1a8ce8', // 亮蓝
  '#4aa8f2', // 天蓝
  '#2dd4bf', // 青绿
  '#4ade80', // 绿
  '#f5a623', // 琥珀
  '#f472b6', // 粉
  '#a78bfa', // 紫
  '#818cf8', // 靛蓝
  '#7cc4f7', // 浅蓝
]

// 标准 12 色环（色相 30° 等分，高辨识度，适合逐柱/逐项着色）
export const WHEEL_12_COLORS = [
  '#e6194b', // 红    0°
  '#f58231', // 橙   30°
  '#e6b800', // 金黄 60°
  '#8bc34a', // 黄绿 90°
  '#3cb44b', // 绿  120°
  '#009e73', // 青绿 150°
  '#42b8d4', // 青  180°
  '#4363d8', // 蓝  210°
  '#7b5cd6', // 蓝紫 240°
  '#911eb4', // 紫  270°
  '#e056fd', // 品红 300°
  '#f03288', // 玫红 330°
]

// 标准 24 色环（色相 15° 等分，高辨识度）
export const WHEEL_24_COLORS = Array.from({ length: 24 }, (_, i) => {
  const h = (i * 15) % 360
  const s = 0.72
  const l = 0.5
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2
  let r = 0, g = 0, b = 0
  if (h < 60) { r = c; g = x; b = 0 }
  else if (h < 120) { r = x; g = c; b = 0 }
  else if (h < 180) { r = 0; g = c; b = x }
  else if (h < 240) { r = 0; g = x; b = c }
  else if (h < 300) { r = x; g = 0; b = c }
  else { r = c; g = 0; b = x }
  const toHex = (v) => Math.round((v + m) * 255).toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
})

// 根据数据条数自动选色：少于12个用标准12色环随机取色，12个及以上用24色环随机取色
export function pickColors(count) {
  const palette = count < 12 ? WHEEL_12_COLORS : WHEEL_24_COLORS
  const shuffled = [...palette].sort(() => Math.random() - 0.5)
  const n = Math.max(count, 1)
  return Array.from({ length: n }, (_, i) => shuffled[i % shuffled.length])
}
