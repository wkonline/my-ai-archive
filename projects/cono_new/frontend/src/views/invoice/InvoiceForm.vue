<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑发票' : '新增发票' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="110px">
        <el-divider content-position="left"><el-icon><Ticket /></el-icon> 发票信息</el-divider>
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
              <el-select v-model="form.contract" filterable :disabled="!form.customer" placeholder="选择未完结发票合同" style="width:100%">
                <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_number" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开票日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="发票金额" required>
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="发票号" required>
              <el-input v-model="form.invoice_number" placeholder="如：INV-2024-001" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="isEdit">
            <el-form-item label="开票人">
              <el-input :model-value="form.invoice_man_name || '-'" disabled />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存发票</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Ticket } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()

// 新增发票时开票日期默认当天
const today = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const form = reactive({
  id: null, customer: null, contract: null, date: today(), amount: 0,
  invoice_number: '', invoice_man_name: ''
})

const customerOptions = ref([])
const contractOptions = ref([])

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/invoice/customers/', { params: { q: q || '' } })
    customerOptions.value = data || []
  } catch {}
}

const onCustomerChange = async (cid) => {
  form.contract = null
  contractOptions.value = []
  try {
    const data = await request.get('/invoice/contracts/', { params: { customer_id: cid } })
    contractOptions.value = data || []
  } catch {}
}

const loadData = async () => {
  if (!isEdit.value) {
    Object.assign(form, { id: null, customer: null, contract: null, date: today(), amount: 0, invoice_number: '', invoice_man_name: '' })
    searchCustomers('')
    return
  }
  try {
    const data = await request.get(`/invoice/${route.params.id}/`)
    Object.assign(form, {
      id: data.id,
      customer: data.customer,
      contract: data.contract,
      date: data.date,
      amount: Number(data.amount),
      invoice_number: data.invoice_number,
      invoice_man_name: data.invoice_man_name || '',
    })
    customerOptions.value = [{ id: data.customer, company_name: data.customer_name }]
    contractOptions.value = [{ id: data.contract, contract_number: data.contract_number }]
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.contract) { ElMessage.warning('请选择合同编号'); return }
  if (!form.date) { ElMessage.warning('请选择开票日期'); return }
  if (!form.invoice_number) { ElMessage.warning('请输入发票号'); return }
  saving.value = true
  try {
    const payload = {
      customer: form.customer,
      contract: form.contract,
      date: form.date,
      amount: form.amount,
      invoice_number: form.invoice_number,
    }
    console.log('Saving invoice:', payload)
    const url = form.id ? `/invoice/${form.id}/` : '/invoice/'
    const method = form.id ? 'put' : 'post'
    const res = await request[method](url, payload)
    console.log('Save response:', res)
    ElMessage.success('保存成功')
    router.push('/invoice')
  } catch (e) {
    console.error('Save error:', e)
    const msg = e?.response?.data?.detail || e?.message || '保存失败，请重试'
    ElMessage.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    saving.value = false
  }
}

const goBack = () => router.push('/invoice')

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
