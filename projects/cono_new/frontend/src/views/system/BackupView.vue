<template>
  <div>
    <el-card shadow="never">
      <template #header><span style="font-size:16px;font-weight:600">数据备份</span></template>
      <p style="color:#909399;font-size:13px;margin-bottom:16px">数据库备份管理，支持创建和恢复备份。</p>
      <el-space>
        <el-button type="primary" @click="createBackup">
          <el-icon><FolderOpened /></el-icon>创建备份
        </el-button>
        <el-button @click="loadBackups">
          <el-icon><Refresh /></el-icon>刷新列表
        </el-button>
      </el-space>
      <el-table :data="backups" stripe border style="margin-top:12px" v-loading="loading">
        <el-table-column prop="name" label="备份名称" min-width="200" />
        <el-table-column prop="size" label="大小" width="100" />
        <el-table-column prop="created" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="restoreBackup(row)">恢复</el-button>
            <el-button link type="danger" size="small" @click="deleteBackup(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened, Refresh } from '@element-plus/icons-vue'
import request from '../../api/request'

const backups = ref([]), loading = ref(false)

// 本地开发：调用后端备份接口（如已实现）
const loadBackups = async () => {
  loading.value = true
  try {
    // 待后端实现 /api/backup/ 接口后启用
    ElMessage.info('备份功能待后端实现 /api/backup/ 接口')
  } finally { loading.value = false }
}
const createBackup = () => {
  ElMessageBox.confirm('确认创建数据库备份？', '提示', { type: 'warning' }).then(() => {
    ElMessage.info('备份功能待后端实现')
  }).catch(() => {})
}
const restoreBackup = (row) => {
  ElMessageBox.confirm(`确认恢复备份 ${row.name}？此操作将覆盖当前数据！`, '警告', { type: 'warning' })
    .then(() => { ElMessage.info('恢复功能待后端实现') })
    .catch(() => {})
}
const deleteBackup = (row) => {
  ElMessageBox.confirm(`确认删除备份 ${row.name}？`, '提示', { type: 'warning' })
    .then(() => { ElMessage.info('删除功能待后端实现') })
    .catch(() => {})
}

onMounted(loadBackups)
</script>
<style scoped></style>
