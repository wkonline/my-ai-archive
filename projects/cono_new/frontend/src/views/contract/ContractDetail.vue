<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">合同详情 - {{ contract.contract_number || '' }}</span>
      </template>
    </el-page-header>

    <!-- 合同基本信息 -->
    <el-card shadow="never" class="section-card" v-loading="loading">
      <template #header>
        <span class="card-title"><el-icon><Briefcase /></el-icon> 合同基本信息</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="合同序号">{{ contract.order_number }}</el-descriptions-item>
        <el-descriptions-item label="合同日期">{{ contract.date }}</el-descriptions-item>
        <el-descriptions-item label="合同数量"><strong>{{ contract.quantity }}</strong></el-descriptions-item>
        <el-descriptions-item label="合同号">
          <el-link type="primary" :underline="false">{{ contract.contract_number }}</el-link>
        </el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ contract.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="业务员">{{ contract.saler_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="合同金额"><strong class="amount">¥{{ Number(contract.total_price || 0).toLocaleString() }}</strong></el-descriptions-item>
        <el-descriptions-item label="货款状态">
          <el-tag :type="contract.payment_completed ? 'success' : 'warning'">{{ contract.payment_completed ? '已结清' : '未结清' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="发票状态">
          <el-tag :type="contract.invoice_completed ? 'success' : 'warning'">{{ contract.invoice_completed ? '已结清' : '未结清' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="发货状态">
          <el-tag :type="deliveryCount > 0 ? 'success' : 'info'">{{ deliveryCount > 0 ? `已发货 (${deliveryCount}条)` : '未发货' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="回款比例"><strong>{{ paymentRatio }}%</strong></el-descriptions-item>
        <el-descriptions-item label="附件">
          <el-link v-if="contract.attachment" @click="openAttachment(contract)" type="success">
            <el-icon><Document /></el-icon>{{ attachmentName }}
          </el-link>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="contract.remark" label="合同备注" :span="3">{{ contract.remark }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 汇总卡片 -->
    <el-row :gutter="12" class="summary-row">
      <el-col :span="6">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-title" style="color:#0078e0"><el-icon><Money /></el-icon> 已回款</div>
          <div class="summary-value" style="color:#31708f">¥{{ Number(contract.total_collection || 0).toLocaleString() }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-title" style="color:#e6a23c"><el-icon><List /></el-icon> 已开票</div>
          <div class="summary-value" style="color:#8a6d3b">¥{{ Number(contract.total_invoice || 0).toLocaleString() }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-title" style="color:#f56c6c"><el-icon><CircleClose /></el-icon> 未回款</div>
          <div class="summary-value" style="color:#a94442">¥{{ Number(contract.outstanding_balance || 0).toLocaleString() }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-title" style="color:#909399"><el-icon><TrendCharts /></el-icon> 回款比例</div>
          <div class="summary-value" style="color:#333">{{ paymentRatio }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 产品明细 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span class="card-title"><el-icon><List /></el-icon> 产品明细</span>
      </template>
      <el-table :data="contractProducts" stripe border size="small">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="category_name" label="产品名称" min-width="140" />
        <el-table-column prop="product_model" label="产品型号" min-width="140" />
        <el-table-column prop="contract_type" label="服务类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.contract_type === 'sale' ? 'success' : 'warning'" size="small">
              {{ row.contract_type === 'sale' ? '销售' : '维修' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column label="单价" width="110" align="right">
          <template #default="{ row }">¥{{ Number(row.price).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">¥{{ Number(row.total_price).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="description" label="备注" min-width="120" show-overflow-tooltip />
      </el-table>
      <div class="table-summary" v-if="contractProducts.length">
        <span>合计：{{ contractProducts.length }} 行</span>
        <span>合同金额：<strong class="amount">¥{{ Number(contract.total_price || 0).toLocaleString() }}</strong></span>
      </div>
    </el-card>

    <!-- 开票记录 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header-row">
          <span class="card-title"><el-icon><Document /></el-icon> 开票记录</span>
          <span class="card-subtitle">共 {{ invoices.length }} 笔，合计 ¥{{ Number(contract.total_invoice || 0).toLocaleString() }} 元</span>
        </div>
      </template>
      <el-table :data="invoices" stripe border size="small">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="customer_name" label="客户名称" min-width="140" />
        <el-table-column prop="invoice_number" label="发票号码" min-width="130" />
        <el-table-column label="开票金额" width="120" align="right">
          <template #default="{ row }"><strong>¥{{ Number(row.amount).toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="invoice_man_name" label="开票人" width="110" />
      </el-table>
      <div v-if="!invoices.length" class="empty-tip">暂无开票记录</div>
    </el-card>

    <!-- 回款记录 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header-row">
          <span class="card-title"><el-icon><Money /></el-icon> 回款记录</span>
          <span class="card-subtitle">共 {{ collections.length }} 笔，合计 ¥{{ Number(contract.total_collection || 0).toLocaleString() }} 元</span>
        </div>
      </template>
      <el-table :data="collections" stripe border size="small">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column prop="customer_name" label="客户名称" min-width="140" />
        <el-table-column label="回款金额" width="120" align="right">
          <template #default="{ row }"><strong>¥{{ Number(row.amount).toLocaleString() }}</strong></template>
        </el-table-column>
        <el-table-column prop="collection_method_display" label="回款方式" width="110" />
      </el-table>
      <div v-if="!collections.length" class="empty-tip">暂无回款记录</div>
    </el-card>

    <!-- 发货记录 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header-row">
          <span class="card-title"><el-icon><Van /></el-icon> 发货记录</span>
          <span class="card-subtitle">共 {{ deliveries.length }} 条</span>
        </div>
      </template>
      <el-table :data="deliveries" stripe border size="small">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column prop="contract_number" label="合同号" min-width="130" />
        <el-table-column prop="date" label="发货日期" width="110" />
        <el-table-column prop="productcategory" label="产品名称" min-width="130" />
        <el-table-column prop="product" label="产品型号" min-width="130" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="delivery_man_name" label="发货人" width="110" />
      </el-table>
      <div v-if="!deliveries.length" class="empty-tip">暂无发货记录</div>
    </el-card>

    <!-- 操作按钮 -->
    <div class="action-row">
      <el-button type="primary" @click="goEdit"><el-icon><Edit /></el-icon> 编辑合同</el-button>
      <el-button @click="goBack"><el-icon><Back /></el-icon> 返回列表</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Briefcase, Document, List, Money, CircleClose, TrendCharts, Van, Edit, Back } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const contract = ref({})
const contractProducts = ref([])
const invoices = ref([])
const collections = ref([])
const deliveries = ref([])
const loading = ref(false)

const deliveryCount = computed(() => deliveries.value.length)
const paymentRatio = computed(() => {
  const total = Number(contract.value.total_price || 0)
  if (!total) return 0
  return Math.round((Number(contract.value.total_collection || 0) / total) * 100)
})
const attachmentName = computed(() => {
  if (!contract.value.attachment) return ''
  return contract.value.attachment.split('/').pop()
})

const loadData = async () => {
  loading.value = true
  try {
    const data = await request.get(`/contract/${route.params.id}/`)
    contract.value = data
    const [cp, inv, col, del] = await Promise.all([
      request.get(`/contract-product/?contract=${route.params.id}&page_size=200`),
      request.get(`/invoice/?contract=${route.params.id}&page_size=200`),
      request.get(`/collection/?contract=${route.params.id}&page_size=200`),
      request.get(`/delivery/?contract=${route.params.id}&page_size=200`),
    ])
    contractProducts.value = cp.results || []
    invoices.value = inv.results || []
    collections.value = col.results || []
    deliveries.value = del.results || []
  } catch {} finally { loading.value = false }
}

const goBack = () => router.push('/contract')
const goEdit = () => router.push(`/contract/edit/${route.params.id}`)

const openAttachment = (row) => {
  if (!row.attachment) return
  // 通过老版站点（端口8000）直接打开附件，绕过新系统媒体卷挂载限制
  window.open(`http://192.168.1.202:8000/media/${row.attachment}`, '_blank')
}

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.section-card { margin-bottom: 16px; }
.section-card :deep(.el-card__header) { padding: 10px 14px; }
.card-title { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; color: #303133; }
.card-header-row { display: flex; align-items: center; justify-content: space-between; }
.card-subtitle { font-size: 12px; color: #909399; font-weight: normal; }
.amount { color: #f56c6c; }
.summary-row { margin-bottom: 16px; }
.summary-card { text-align: center; }
.summary-title { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.summary-value { font-size: 22px; font-weight: 700; }
.table-summary {
  display: flex; justify-content: flex-end; gap: 24px;
  margin-top: 8px; padding: 8px 12px;
  background: #f4f6f9; border-radius: 4px; font-size: 13px; color: #606266;
}
.empty-tip { text-align: center; color: #909399; padding: 20px 0; font-size: 13px; }
.action-row { display: flex; gap: 8px; margin-top: 8px; }
</style>
