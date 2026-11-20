<template>
  <div>
    <el-card shadow="never">
      <template #header><span style="font-size:16px;font-weight:600">数据备份与恢复</span></template>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <el-button type="primary" :loading="creating" @click="doCreate">
          <el-icon><FolderOpened /></el-icon>创建备份
        </el-button>
        <el-button @click="loadBackups" :loading="loading">
          <el-icon><Refresh /></el-icon>刷新列表
        </el-button>
      </div>
      <el-table :data="backups" stripe border v-loading="loading">
        <el-table-column prop="name" label="备份文件" min-width="240">
          <template #default="{ row }">{{ row.name }}</template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="90" align="right" />
        <el-table-column prop="created" label="创建时间" width="120" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" :loading="restoring === row.name"
              @click="doRestore(row)">恢复</el-button>
            <el-button link type="danger" size="small" :loading="deleting === row.name"
              @click="doDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!backups.length && !loading" class="empty-tip">暂无备份记录，点击「创建备份」生成第一条。</div>
    </el-card>

    <!-- 恢复进度弹窗 -->
    <el-dialog v-model="restoreDialogVisible" title="数据库恢复" width="460px" :close-on-click-away="false">
      <div style="padding:10px 0">
        <el-progress v-if="restoreRunning" :percentage="restorePercent" :stroke-width="14" />
        <p style="margin-top:14px;color:#606266;font-size:13px">{{ restoreMsg }}</p>
      </div>
      <template #footer>
        <el-button v-if="!restoreRunning" type="primary" @click="restoreDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened, Refresh } from '@element-plus/icons-vue'
import request from '../../api/request'

const backups = ref([])
const loading = ref(false)
const creating = ref(false)
const restoring = ref(null)
const deleting = ref(null)
const restoreDialogVisible = ref(false)
const restoreRunning = ref(false)
const restorePercent = ref(0)
const restoreMsg = ref('')

let pollTimer = null

const loadBackups = async () => {
  loading.value = true
  try {
    const data = await request.get('/backup/list/')
    backups.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error(e)
  } finally { loading.value = false }
}

const doCreate = async () => {
  try {
    await ElMessageBox.confirm('确认创建数据库备份？此操作需要数分钟。', '提示', { type: 'warning' })
  } catch { return }
  creating.value = true
  try {
    const res = await request.post('/backup/create/')
    ElMessage.success(res.message || '备份创建成功')
    loadBackups()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '备份失败')
  } finally { creating.value = false }
}

const doRestore = async (row) => {
  try {
    await ElMessageBox.confirm(`确认从「${row.name}」恢复数据库？\n当前所有数据将被覆盖，请谨慎操作！`, '严重警告', {
      type: 'error', confirmButtonText: '确认恢复', cancelButtonText: '取消',
      distinguishCancelAndClose: true,
    })
  } catch { return }
  restoring.value = row.name
  restoreDialogVisible.value = true
  restoreRunning.value = true
  restorePercent.value = 10
  restoreMsg.value = `正在后台恢复 ${row.name}，完成后将自动提示…`
  try {
    const res = await request.post('/backup/restore/', { name: row.name })
    const jobId = res.job_id
    if (!jobId) {
      restoreRunning.value = false
      restorePercent.value = 100
      restoreMsg.value = res.message || '恢复完成'
      ElMessage.success('恢复成功')
      return
    }
    restorePercent.value = 30
    let tries = 0
    pollTimer = setInterval(async () => {
      tries += 1
      try {
        const st = await request.get('/backup/restore/status/', { params: { job_id: jobId } })
        if (st.status === 'success') {
          clearInterval(pollTimer)
          pollTimer = null
          restoreRunning.value = false
          restorePercent.value = 100
          restoreMsg.value = '恢复完成，已覆盖当前数据'
          ElMessage.success('恢复成功')
        } else if (st.status === 'error') {
          clearInterval(pollTimer)
          pollTimer = null
          restoreRunning.value = false
          restorePercent.value = 100
          restoreMsg.value = '恢复失败：' + (st.detail || '未知错误')
          ElMessage.error('恢复失败：' + (st.detail || '未知错误'))
        } else {
          restorePercent.value = Math.min(90, 30 + tries * 3)
        }
      } catch (e) {
        if (tries > 60) {
          clearInterval(pollTimer)
          pollTimer = null
          restoreRunning.value = false
          restoreMsg.value = '无法获取恢复状态，请稍后重试'
        }
      }
    }, 2000)
  } catch (e) {
    restoreRunning.value = false
    restorePercent.value = 100
    restoreMsg.value = '恢复启动失败：' + (e?.response?.data?.detail || '未知错误')
    ElMessage.error('恢复失败')
  } finally {
    restoring.value = null
  }
}

const doDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除备份「${row.name}」？`, '提示', { type: 'warning' })
  } catch { return }
  deleting.value = row.name
  try {
    await request.delete('/backup/delete/', { data: { name: row.name } })
    ElMessage.success('已删除')
    loadBackups()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  } finally { deleting.value = null }
}

onMounted(loadBackups)
</script>

<style scoped>
.empty-tip { color: #909399; padding: 24px 0; text-align: center; font-size: 13px; }
</style>
