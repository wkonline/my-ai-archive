<template>
  <el-tabs :model-value="active" class="flow-tabs" @tab-change="go">
    <el-tab-pane label="产品档案" name="archive" />
    <el-tab-pane label="寄给客户登记" name="out" />
    <el-tab-pane label="客户返回登记" name="return" />
  </el-tabs>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

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
