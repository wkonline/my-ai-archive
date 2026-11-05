<template>
  <div>
    <el-card shadow="never" class="chart-card">
      <h3 style="margin:0 0 12px;font-size:16px;color:#303133">应收应付统计</h3>
      <el-row :gutter="12">
        <el-col :span="8">
          <el-statistic title="合同总金额" :value="stats.total_amount" prefix="¥" :precision="2" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="已回款金额" :value="stats.total_collection" prefix="¥" :precision="2" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="未回款金额" :value="stats.pending_amount" prefix="¥" :precision="2" value-style="color:#e6a23c" />
        </el-col>
      </el-row>
    </el-card>
    <el-card shadow="never">
      <h4 style="margin:0 0 12px;font-size:14px">各合同回款进度</h4>
      <el-table :data="contracts" stripe border v-loading="loading">
        <el-table-column prop="contract_number" label="合同编号" min-width="130" />
        <el-table-column prop="customer_name" label="客户名称" min-width="150" />
        <el-table-column label="合同金额" width="130" align="right">
          <template #default="{ row }">¥{{ Number(row.total_price).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="已回款" width="130" align="right">
          <template #default="{ row }">¥{{ Number(row.total_collection || 0).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="回款进度" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.payment_ratio || 0" :stroke-width="8" :status="row.payment_completed ? 'success' : ''" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import request from '../../api/request'
const contracts = ref([]), stats = ref({ total_amount: 0, total_collection: 0, pending_amount: 0 }), loading = ref(false)
const fetchAll = async () => {
  loading.value = true
  try {
    const [statsData, listData] = await Promise.all([
      request.get('/contract/stats/'),
      request.get('/contract/?page_size=100')
    ])
    stats.value = {
      total_amount: Number(statsData.total_amount || 0),
      total_collection: 0,
      pending_amount: 0,
    }
    contracts.value = listData.results || []
    let totalCol = 0
    contracts.value.forEach(r => { totalCol += Number(r.total_collection || 0) })
    stats.value.total_collection = totalCol
    stats.value.pending_amount = stats.value.total_amount - totalCol
  } finally { loading.value = false }
}
onMounted(fetchAll)
</script>
<style scoped>
.chart-card { margin-bottom: 12px; }
</style>
