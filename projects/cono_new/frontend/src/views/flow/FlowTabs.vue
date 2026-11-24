<template>
  <el-tabs :model-value="active" class="flow-tabs" @tab-change="go">
    <el-tab-pane v-for="t in tabs" :key="t.name" :label="t.label" :name="t.name" />
  </el-tabs>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { hasPerm } from '../../utils/perm'

const route = useRoute()
const router = useRouter()

// 只显示当前用户有权限的栏目，避免点进去被拦回首页
const ALL_TABS = [
  { name: 'archive', label: '产品档案', perm: 'flow_archive_list' },
  { name: 'out', label: '寄给客户登记', perm: 'flow_out_list' },
  { name: 'return', label: '客户返回登记', perm: 'flow_return_list' },
]
const tabs = computed(() => ALL_TABS.filter(t => hasPerm(t.perm)))

const active = computed(() => {
  const path = route.path
  if (path.startsWith('/flow/out')) return 'out'
  if (path.startsWith('/flow/return')) return 'return'
  return 'archive'
})

const go = (name) => router.push(`/flow/${name}`)
</script>

<style scoped>
.flow-tabs { margin-bottom: 4px; }
</style>
