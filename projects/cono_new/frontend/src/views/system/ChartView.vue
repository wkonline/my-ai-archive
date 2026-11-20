<template>
  <div class="ar-page">
    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-warn">
          <div class="stat-value">{{ ar.invoiced_unpaid_count }}</div>
          <div class="stat-label">开票未付款</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-info">
          <div class="stat-value">¥{{ ar.total_invoiced_outstanding.toFixed(2) }}</div>
          <div class="stat-label">开票应收余额</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-warn">
          <div class="stat-value">{{ ar.uninvoiced_unpaid_count }}</div>
          <div class="stat-label">未开票未付款</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-info">
          <div class="stat-value">¥{{ ar.total_uninvoiced_outstanding.toFixed(2) }}</div>
          <div class="stat-label">未开票应收余额</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选工具栏 -->
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar-row">
        <el-form :model="filter" inline class="search-form" label-width="80px">
          <el-form-item label="客户名称">
            <el-input v-model="filter.customer_name" placeholder="输入客户名称关键词" clearable style="width:200px" @keyup.enter="fetchAr" />
          </el-form-item>
          <el-form-item label="业务员">
            <el-select v-model="filter.salesperson" placeholder="全部业务员" filterable style="width:160px">
              <el-option :label="s.username" :value="s.id" v-for="s in ar.salespeople" :key="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button @click="fetchAr"><el-icon><Search /></el-icon>&nbsp;查询</el-button>
            <el-button @click="resetFilter"><el-icon><Refresh /></el-icon>&nbsp;重置</el-button>
          </el-form-item>
        </el-form>
        <span class="spacer"></span>
        <div class="toolbar-summary">
          <span class="summary-item"><strong>开票未付款：</strong>{{ ar.invoiced_unpaid_count }} 单，余额 ¥{{ ar.total_invoiced_outstanding.toFixed(2) }}</span>
          <span class="summary-item"><strong>未开票未付款：</strong>{{ ar.uninvoiced_unpaid_count }} 单，余额 ¥{{ ar.total_uninvoiced_outstanding.toFixed(2) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 开票未付款合同 -->
    <el-card shadow="never" class="panel-card">
      <div class="panel-header">
        <span class="panel-title">开票未付款合同</span>
        <span class="panel-count">{{ ar.invoiced_unpaid_count }} 单</span>
      </div>
      <el-table :data="ar.invoiced_unpaid" row-key="id" stripe border v-loading="loading">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ row }">{{ row.seq }}</template>
        </el-table-column>
        <el-table-column prop="contract_number" label="合同号" width="135">
          <template #default="{ row }">
            <router-link :to="`/contract/${row.id}`" class="link-cell">{{ row.contract_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="合同日期" width="105" />
        <el-table-column prop="customer_name" label="客户名称" show-overflow-tooltip />
        <el-table-column prop="saler_name" label="业务员" width="100" />
        <el-table-column label="合同金额" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.total_price).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="已开票" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.invoiced_amount).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="已回款" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.collected_amount).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="应收余额" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.outstanding_balance).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column prop="last_invoice_date" label="最后开票日期" width="120" />
        <el-table-column label="开票比例" width="100" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }"><el-progress :percentage="Number(row.invoice_ratio) || 0" :stroke-width="8" /></template>
        </el-table-column>
        <el-table-column label="回款比例" width="100" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }"><el-progress :percentage="Number(row.collection_ratio) || 0" :stroke-width="8" /></template>
        </el-table-column>
      </el-table>
      <div v-if="ar.invoiced_unpaid.length === 0" class="empty-tip">暂无开票未付款合同</div>
    </el-card>

    <!-- 未开票未付款合同 -->
    <el-card shadow="never" class="panel-card">
      <div class="panel-header">
        <span class="panel-title">未开票未付款合同</span>
        <span class="panel-count">{{ ar.uninvoiced_unpaid_count }} 单</span>
      </div>
      <el-table :data="ar.uninvoiced_unpaid" row-key="id" stripe border v-loading="loading">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ row }">{{ row.seq }}</template>
        </el-table-column>
        <el-table-column prop="contract_number" label="合同号" width="135">
          <template #default="{ row }">
            <router-link :to="`/contract/${row.id}`" class="link-cell">{{ row.contract_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="合同日期" width="105" />
        <el-table-column prop="customer_name" label="客户名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="saler_name" label="业务员" width="100" />
        <el-table-column label="合同金额" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.total_price).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="已开票" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.invoiced_amount).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="已回款" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.collected_amount).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column label="应收余额" width="115" align="right">
          <template #default="{ row }">¥{{ Number(row.outstanding_balance).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</template>
        </el-table-column>
        <el-table-column prop="last_invoice_date" label="最后开票日期" width="120" />
        <el-table-column label="开票比例" width="100" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }"><el-progress :percentage="Number(row.invoice_ratio) || 0" :stroke-width="8" /></template>
        </el-table-column>
        <el-table-column label="回款比例" width="100" align="center" :show-overflow-tooltip="false">
          <template #default="{ row }"><el-progress :percentage="Number(row.collection_ratio) || 0" :stroke-width="8" /></template>
        </el-table-column>
      </el-table>
      <div v-if="ar.uninvoiced_unpaid.length === 0" class="empty-tip">暂无未开票未付款合同</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import request from '../../api/request'

const loading = ref(false)
const filter = reactive({ customer_name: '', salesperson: '' })
const ar = ref({
  invoiced_unpaid: [],
  uninvoiced_unpaid: [],
  invoiced_unpaid_count: 0,
  uninvoiced_unpaid_count: 0,
  total_invoiced_outstanding: 0,
  total_uninvoiced_outstanding: 0,
  salespeople: [],
  selected_salesperson: '',
  selected_customer_name: '',
})

const fetchAr = async () => {
  loading.value = true
  try {
    const res = await request.get('/contract/ar/', { params: filter })
    ar.value = {
      invoiced_unpaid: (res.invoiced_unpaid || []).map((item, idx) => ({ ...item, seq: idx + 1 })),
      uninvoiced_unpaid: (res.uninvoiced_unpaid || []).map((item, idx) => ({ ...item, seq: idx + 1 })),
      invoiced_unpaid_count: res.invoiced_unpaid_count || 0,
      uninvoiced_unpaid_count: res.uninvoiced_unpaid_count || 0,
      total_invoiced_outstanding: Number(res.total_invoiced_outstanding || 0),
      total_uninvoiced_outstanding: Number(res.total_uninvoiced_outstanding || 0),
      salespeople: res.salespeople || [],
      selected_salesperson: res.selected_salesperson || '',
      selected_customer_name: res.selected_customer_name || '',
    }
    filter.customer_name = ar.value.selected_customer_name
    filter.salesperson = ar.value.selected_salesperson
  } catch (e) {
    ElMessage.error('获取应收应付数据失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filter.customer_name = ''
  filter.salesperson = ''
  fetchAr()
}

onMounted(fetchAr)
</script>

<style scoped>
.ar-page { padding: 0 16px 24px; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-main); margin-bottom: 4px; }
.stat-label { font-size: 13px; color: #606266; }
.stat-warn .stat-value { color: #e6a23c; }
.stat-info .stat-value { color: #1989fa; }
.toolbar-card { margin-bottom: 16px; }
.toolbar-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.spacer { flex: 1; }
.toolbar-summary { font-size: 13px; color: #606266; display: flex; gap: 20px; align-items: center; }
.panel-card { margin-bottom: 16px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid #ebeef5; background: #f4f6f8; margin: -1px -1px 0 -1px; }
.panel-title { font-size: 15px; font-weight: 700; color: var(--text-main); }
.panel-count { font-size: 13px; color: #606266; background: #eef2f7; padding: 3px 10px; border-radius: 10px; }
.empty-tip { padding: 24px 0; color: #909399; text-align: center; }
.link-cell { color: #409eff; text-decoration: none; }
.link-cell:hover { text-decoration: underline; }
</style>
