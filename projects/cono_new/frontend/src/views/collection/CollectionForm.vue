<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑回款' : '新增回款' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="110px">
        <el-divider content-position="left"><el-icon><Money /></el-icon> 回款信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers" placeholder="请输入客户名称" style="width:100%" @change="onCustomerChange">
                <el-option v-for="c in customerOptions" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="合同编号" required>
              <el-select v-model="form.contract" filterable :disabled="!form.customer" placeholder="选择欠款合同" style="width:100%" @change="onContractChange">
                <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_number" :value="c.id">
                  <span>{{ c.contract_number }}</span>
                  <span style="float:right;color:#f56c6c">欠款 ¥{{ Number(c.balance || 0).toLocaleString() }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="回款日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="回款金额" required>
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="回款方式">
              <el-select v-model="form.collection_method" style="width:100%">
                <el-option v-for="(label, val) in collectionMethods" :key="val" :label="label" :value="Number(val)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="isEdit">
            <el-form-item label="当前已回款">
              <el-input :model-value="`¥${Number(form.current_collection || 0).toLocaleString()}`" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存回款</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Money } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()

const collectionMethods = { 1: '电汇', 2: '银承', 3: '现金', 4: '万纳信', 5: '迪链' }

// 新增回款时日期默认当天
const today = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const form = reactive({
  id: null, customer: null, contract: null, date: today(), amount: 0,
  collection_method: 1, current_collection: 0
})

const customerOptions = ref([])
const contractOptions = ref([])

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/collection/customers/', { params: { q: q || '' } })
    customerOptions.value = data || []
  } catch {}
}

const onCustomerChange = async (cid) => {
  form.contract = null
  form.amount = 0
  contractOptions.value = []
  try {
    const data = await request.get('/collection/contracts/', { params: { customer_id: cid } })
    contractOptions.value = data || []
  } catch {}
}

const onContractChange = (cid) => {
  const c = contractOptions.value.find(i => i.id === cid)
  if (c) form.amount = Number(c.balance || 0)
}

const loadData = async () => {
  if (!isEdit.value) {
    Object.assign(form, { id: null, customer: null, contract: null, date: today(), amount: 0, collection_method: 1, current_collection: 0 })
    searchCustomers('')
    return
  }
  try {
    const data = await request.get(`/collection/${route.params.id}/`)
    Object.assign(form, {
      id: data.id,
      customer: data.customer,
      contract: data.contract,
      date: data.date,
      amount: Number(data.amount),
      collection_method: data.collection_method,
      current_collection: Number(data.contract_total_price || 0) - Number(data.contract_balance || 0),
    })
    customerOptions.value = [{ id: data.customer, company_name: data.customer_name }]
    contractOptions.value = [{ id: data.contract, contract_number: data.contract_number, balance: data.contract_balance }]
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.contract) { ElMessage.warning('请选择合同编号'); return }
  if (!form.date) { ElMessage.warning('请选择回款日期'); return }
  saving.value = true
  try {
    const payload = {
      customer: form.customer,
      contract: form.contract,
      date: form.date,
      amount: form.amount,
      collection_method: form.collection_method,
    }
    if (form.id) await request.put(`/collection/${form.id}/`, payload)
    else await request.post('/collection/', payload)
    ElMessage.success('保存成功')
    router.push('/collection')
  } finally {
    saving.value = false
  }
}

const goBack = () => router.push('/collection')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.form-card :deep(.el-form) { width: 100%; }
.footer-actions {
  margin-top: 20px; padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  display: flex; justify-content: flex-end; gap: 8px;
}
</style>
