<template>
  <div class="ann-content" v-html="html"></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  content: { type: String, default: '' },
})

const escapeHtml = (text) => String(text)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;')

// 匹配 http(s):// 绝对地址和以 / 开头的站内路径。
// 站内路径必须限定后缀，否则正文里的「3/5」这种分数也会被当成链接。
const URL_RE = /(https?:\/\/[^\s<>"'）)]+|\/(?:api\/)?[\w\-./]*\/(?:download|media)\/?[^\s<>"'）)]*)/g

const linkify = (text) => {
  let result = ''
  let last = 0
  let m
  URL_RE.lastIndex = 0
  while ((m = URL_RE.exec(text)) !== null) {
    result += escapeHtml(text.slice(last, m.index))
    const url = m[0]
    result += `<a class="ann-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>`
    last = m.index + url.length
  }
  return result + escapeHtml(text.slice(last))
}

// 正文按纯文本存储（换行靠 pre-wrap），这里只做链接识别，
// 不解析 Markdown/HTML，避免公告里写个 <script> 就被执行。
const html = computed(() => linkify(props.content || ''))
</script>

<style scoped>
.ann-content {
  font-size: 14px;
  line-height: 1.9;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
.ann-content :deep(.ann-link) {
  color: var(--el-color-primary);
  text-decoration: none;
  border-bottom: 1px dashed currentColor;
}
.ann-content :deep(.ann-link:hover) { color: var(--el-color-primary-light-3); }
</style>
