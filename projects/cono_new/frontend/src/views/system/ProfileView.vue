<template>
  <div class="profile-page">
    <!-- 左侧：个人信息卡片 + 快捷操作 + 我的数据 -->
    <div class="profile-left">
      <el-card shadow="never" class="info-card">
        <div class="avatar-wrap">
          <div class="avatar-circle">{{ initials }}</div>
        </div>
        <h3 class="user-name">{{ user?.username || '-' }}</h3>
        <p class="user-desc">
          <el-tag :type="roleTagType(user?.role)">{{ roleLabel(user?.role) }}</el-tag>
          <el-tag size="small">{{ user?.department_name || '-' }}</el-tag>
        </p>
        <hr class="profile-hr" />
        <dl class="info-list">
          <dt>姓名</dt><dd>{{ user?.username || '-' }}</dd>
          <dt>性别</dt><dd>{{ genderLabel(user?.gender) }}</dd>
          <dt>手机</dt><dd>{{ user?.phone || '-' }}</dd>
          <dt>入职时间</dt><dd>{{ formatDate(user?.create_date) }}</dd>
        </dl>
      </el-card>

      <el-card shadow="never" class="quick-card">
        <div class="card-title">
          <el-icon><Tools /></el-icon><span>快捷操作</span>
        </div>
        <div class="quick-actions">
          <el-button type="primary" plain @click="goPage('/user/profile/edit')">
            <el-icon class="btn-ico"><Edit /></el-icon><span class="btn-text">修改资料</span>
          </el-button>
          <el-button type="warning" plain @click="goPage('/user/profile/password')">
            <el-icon class="btn-ico"><Lock /></el-icon><span class="btn-text">修改密码</span>
          </el-button>
          <el-button plain @click="router.push('/')">
            <el-icon class="btn-ico"><HomeFilled /></el-icon><span class="btn-text">返回首页</span>
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="stats-card">
        <div class="card-title">
          <el-icon><Monitor /></el-icon><span>我的数据</span>
        </div>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-number">{{ stats?.total_contracts ?? 0 }}</div>
            <div class="stat-label">合同</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats?.total_plans ?? 0 }}</div>
            <div class="stat-label">计划</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats?.total_services ?? 0 }}</div>
            <div class="stat-label">售后</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 右侧：详细信息 + 最近操作日志 -->
    <div class="profile-right">
      <el-card shadow="never" class="detail-card">
        <div class="card-title">
          <el-icon><UserFilled /></el-icon><span>详细信息</span>
        </div>
        <el-table :data="detailRows" border size="small" class="detail-table" row-key="label">
          <el-table-column prop="label" label="字段" min-width="120" align="center" />
          <el-table-column prop="value" label="内容" min-width="200" show-overflow-tooltip />
        </el-table>
      </el-card>

      <el-card shadow="never" class="log-card">
        <div class="card-header">
          <span class="card-title">
            <el-icon><Clock /></el-icon> 最近操作日志
          </span>
          <span class="log-count">共 {{ logs?.length || 0 }} 条</span>
        </div>
        <el-table :data="logs" border size="small" class="log-table" row-key="index">
          <el-table-column label="#" width="60" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="操作时间" width="120">
            <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
          </el-table-column>
          <el-table-column label="操作内容" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ row.action || '-' }}</template>
          </el-table-column>
        </el-table>
        <div v-if="!logs?.length" class="empty-log">暂无操作记录</div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit, Lock, HomeFilled, UserFilled, Tools, Monitor, Clock } from '@element-plus/icons-vue'
import request from '../../api/request'

const router = useRouter()

const roleMap = { admin: '管理员', saler: '业务员', servicer: '客户经理', upkeeper: '售后服务', finance: '财务经理' }
const genderMap = { 1: '男', 2: '女' }
const roleLabel = (r) => roleMap[r] || r || '-'
const genderLabel = (g) => genderMap[g] || '-'
const roleTagType = (r) => {
  const m = { admin: 'danger', saler: 'primary', servicer: 'success', upkeeper: 'info', finance: 'warning' }
  return m[r] || 'info'
}
const formatDate = (t) => t ? String(t).slice(0, 10) : '-'
const formatTime = (t) => t ? String(t).slice(0, 19).replace('T', ' ') : '-'

const initials = computed(() => {
  const name = user.value?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const user = computed(() => JSON.parse(localStorage.getItem('user_info') || '{}'))
const stats = computed(() => user.value?.stats || {})
const logs = ref([])

const detailRows = computed(() => {
  const u = user.value || {}
  return [
    { label: '用户ID', value: String(u.id ?? '-') },
    { label: '用户名', value: u.username || '-' },
    { label: '角色', value: roleLabel(u.role) },
    { label: '部门', value: u.department_name || '-' },
    { label: '性别', value: genderLabel(u.gender) },
    { label: '身份证号', value: u.id_number || '-' },
    { label: '手机', value: u.phone || '-' },
    { label: '地址', value: u.address || '-' },
    { label: '入职时间', value: formatDate(u.create_date) },
    { label: '最后登录', value: '-' },
  ]
})

const goPage = (path) => router.push(path)

const fetchProfile = async () => {
  try {
    const data = await request.get('/user/me')
    if (data) {
      localStorage.setItem('user_info', JSON.stringify(data))
    }
  } catch {}
}

const fetchLogs = async () => {
  try {
    // 用“我的日志”接口：普通用户没有 get_log 权限，直接请求 /log/ 会 403 弹错
    const data = await request.get('/log/mine/')
    const list = data?.results || data || []
    logs.value = list.slice(0, 10).map((l, i) => ({ ...l, index: i }))
  } catch {}
}

onMounted(async () => {
  await fetchProfile()
  await fetchLogs()
})
</script>

<style scoped>
.profile-page {
  display: flex;
  gap: 24px;
  min-height: 100%;
}
.profile-left {
  width: 320px;
  flex-shrink: 0;
}
.profile-right {
  flex: 1;
}

/* 左侧卡片 */
.info-card { margin-bottom: 16px; }
.avatar-wrap { text-align: center; margin-bottom: 12px; }
.avatar-circle {
  width: 80px; height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0078e0, #67c23a);
  color: #fff;
  line-height: 80px;
  font-size: 32px;
  font-weight: 600;
  margin: 0 auto 10px;
}
.user-name { font-size: 18px; font-weight: 600; margin: 0 0 6px; text-align: center; color: var(--text-main); }
.user-desc { text-align: center; font-size: 13px; margin-bottom: 14px; }
.profile-hr { border: none; border-top: 1px solid var(--border); margin: 10px 0; }
.info-list { margin: 0; padding: 0; }
.info-list dt { font-size: 12px; color: var(--text-sub); margin: 8px 0 2px; }
.info-list dd { font-size: 14px; color: var(--text-main); margin: 0 0 8px; padding: 0; }

/* 快捷操作 —— 等宽等高，内容统一左对齐，避免错位 */
.quick-card { margin-bottom: 16px; }
.card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: var(--text-main);
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.quick-actions .el-button {
  width: 100%;
  height: 36px;
  margin: 0;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  box-sizing: border-box;
  border-radius: 4px;
}
.quick-actions .btn-ico { margin-right: 8px; }
.quick-actions .btn-text { line-height: 1; }

/* 统计卡片 */
.stats-row { display: flex; gap: 12px; }
.stat-item {
  flex: 1; background: var(--navy-50);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 8px; text-align: center;
}
.stat-number { font-size: 20px; font-weight: 700; color: var(--navy-600); }
.stat-label { font-size: 12px; color: var(--text-sub); margin-top: 4px; }

/* 右侧卡片 */
.detail-card, .log-card { margin-bottom: 16px; }
.card-header {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 14px; font-weight: 600; color: var(--text-main);
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.log-count { font-size: 13px; color: var(--text-sub); font-weight: normal; }
.empty-log { padding: 30px 0; text-align: center; color: var(--text-sub); font-size: 13px; }

/* el-table 内边距收紧，适配右侧窄列 */
:deep(.el-table th), :deep(.el-table td) {
  font-size: 13px;
  padding: 6px 0;
}
</style>
