<template>
  <div v-if="items.length" class="ann-attach-list">
    <div class="ann-attach-head">
      <el-icon><Paperclip /></el-icon>
      <span>附件（{{ items.length }}）</span>
    </div>
    <ul class="ann-attach-items">
      <li v-for="att in items" :key="att.id" class="ann-attach-item">
        <span class="ann-attach-icon" :class="`ext-${extLabel(att.ext).toLowerCase()}`">{{ extLabel(att.ext) }}</span>
        <div class="ann-attach-info">
          <a class="ann-attach-name" :href="att.download_url" :download="att.name" :title="att.name">
            {{ att.name }}
          </a>
          <span class="ann-attach-size">{{ formatSize(att.size) }}</span>
        </div>
        <el-button class="ann-attach-dl" link type="primary" @click="download(att)">
          <el-icon><Download /></el-icon>&nbsp;下载
        </el-button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { Paperclip, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineProps({
  items: { type: Array, default: () => [] },
})

// 扩展名 -> 短标签，比通用图标更能让人一眼认出是 Word 还是 PDF
const EXT_LABELS = {
  doc: 'DOC', docx: 'DOC', xls: 'XLS', xlsx: 'XLS', ppt: 'PPT', pptx: 'PPT',
  pdf: 'PDF', zip: 'ZIP', rar: 'RAR', '7z': '7Z', txt: 'TXT', csv: 'CSV',
  png: 'PNG', jpg: 'JPG', jpeg: 'JPG', gif: 'GIF',
}
const extLabel = (ext) => EXT_LABELS[String(ext || '').toLowerCase()] || '文件'

const formatSize = (bytes) => {
  const n = Number(bytes) || 0
  if (n <= 0) return ''
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

// 用隐藏链接触发下载：直接 window.open 遇到下载接口返回 401 时只会开个空白页，
// 这里走同源请求，浏览器能正常带上 cookie/并把 Content-Disposition 当成下载处理。
const download = (att) => {
  const a = document.createElement('a')
  a.href = att.download_url
  a.download = att.name
  document.body.appendChild(a)
  a.click()
  a.remove()
  ElMessage.success(`开始下载：${att.name}`)
}
</script>

<style scoped>
.ann-attach-list {
  margin-top: 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: var(--el-fill-color-blank);
  overflow: hidden;
}
.ann-attach-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.ann-attach-items { list-style: none; margin: 0; padding: 6px; }
.ann-attach-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background .18s;
}
.ann-attach-item:hover { background: var(--el-fill-color-light); }
.ann-attach-item + .ann-attach-item { border-top: 1px dashed var(--el-border-color-lighter); }

.ann-attach-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .2px;
  color: #fff;
  background: var(--el-color-info);
}
/* 常见格式按 Office 配色区分，扫一眼就知道是什么文件 */
.ext-doc { background: #2b579a; }
.ext-xls { background: #217346; }
.ext-ppt { background: #b7472a; }
.ext-pdf { background: #c0392b; }
.ext-zip, .ext-rar, .ext-7z { background: #8e6e3c; }
.ext-png, .ext-jpg, .ext-gif { background: #7b5ea7; }
.ext-txt, .ext-csv { background: #5a6b7b; }

.ann-attach-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.ann-attach-name {
  font-size: 13px;
  color: var(--el-color-primary);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ann-attach-name:hover { text-decoration: underline; }
.ann-attach-size { font-size: 12px; color: var(--el-text-color-secondary); }
.ann-attach-dl { flex-shrink: 0; }
</style>
