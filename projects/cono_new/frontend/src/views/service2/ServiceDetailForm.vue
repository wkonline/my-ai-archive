<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ pageTitle }}</span>
      </template>
    </el-page-header>

    <!-- 批量登记 -->
    <el-card v-if="isBatch" shadow="never" class="form-card">
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="batchCustomer" filterable remote :remote-method="searchCustomers" style="width:100%" @change="loadBatchServices">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="完成时间" required>
              <el-date-picker v-model="batchDate" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <el-table :data="batchServices" stripe border size="small" v-loading="batchLoading">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="service_number" label="维修编号" min-width="130" />
        <el-table-column prop="productcategory__name" label="产品名称" min-width="140" />
        <el-table-column prop="product__model" label="产品型号" min-width="130" />
        <el-table-column label="故障现象" min-width="200">
          <template #default="{ row }"><el-input v-model="row.fault_text" placeholder="填写故障现象" /></template>
        </el-table-column>
        <el-table-column label="故障原因" min-width="200">
          <template #default="{ row }"><el-input v-model="row.fault_reason" placeholder="填写故障原因" /></template>
        </el-table-column>
        <el-table-column label="维修方法" min-width="200">
          <template #default="{ row }"><el-input v-model="row.repair_method" placeholder="填写维修方法" /></template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="100" align="center" fixed="right">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="removeBatchRow($index)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="batch-hint">选择客户后自动带出待维修产品，填写故障现象、故障原因、维修方法。</div>
      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="success" :loading="batchSaving" @click="handleBatchSave">保存批量登记</el-button>
      </div>
    </el-card>

    <!-- 知识库搜索 -->
    <el-card v-else-if="isKnowledge" shadow="never" class="form-card">
      <div class="kb-search">
        <el-input v-model="kbQuery" placeholder="输入故障现象/原因/型号关键词" clearable style="width:400px" @keyup.enter="searchKnowledge">
          <template #append><el-button type="primary" @click="searchKnowledge"><el-icon><Search /></el-icon>&nbsp;查询知识库</el-button></template>
        </el-input>
      </div>
      <el-card v-if="kbData.summary" shadow="never" class="kb-summary">
        <el-row :gutter="16">
          <el-col :span="12">
            <h4 class="kb-col-title">常见故障原因</h4>
            <div v-for="item in kbData.summary.reasons" :key="item.text" class="kb-item">{{ item.text }}</div>
          </el-col>
          <el-col :span="12">
            <h4 class="kb-col-title">推荐维修方法</h4>
            <div v-for="item in kbData.summary.methods" :key="item.text" class="kb-item">{{ item.text }}</div>
          </el-col>
        </el-row>
      </el-card>
      <div v-if="kbData.cases && kbData.cases.length" class="kb-cases">
        <h4 class="kb-col-title">相似历史维修记录（{{ kbData.cases.length }} 条）</h4>
        <div v-for="caseItem in kbData.cases" :key="caseItem.service_number + caseItem.repair_date" class="kb-case">
          <div class="kb-case-head">
            <span><el-icon><Document /></el-icon> {{ caseItem.service_number }} <span class="kb-meta">{{ caseItem.customer_name }} / {{ caseItem.product_model }} / {{ caseItem.repair_date }}</span></span>
          </div>
          <div class="kb-field"><b>故障现象：</b>{{ caseItem.fault_text }}</div>
          <div class="kb-field"><b>故障原因：</b>{{ caseItem.fault_reason }}</div>
          <div class="kb-field"><b>维修方法：</b>{{ caseItem.repair_method }}</div>
        </div>
      </div>
      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
      </div>
    </el-card>

    <!-- 单个新增/编辑 -->
    <el-card v-else shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Tools /></el-icon> 维修记录信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers" style="width:100%" @change="onCustomerChange">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维修编号" required>
              <el-select v-model="form.service" filterable style="width:100%" @change="onServiceChange">
                <el-option v-for="s in services" :key="s.id" :label="serviceLabel(s)" :value="s.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称" required>
              <el-input :model-value="form.productcategory_name" disabled placeholder="选择维修编号后自动带出" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号">
              <el-input :model-value="form.product_model" disabled placeholder="选择维修编号后自动带出" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="故障现象" required>
              <el-input v-model="form.fault_text" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="故障原因" required>
              <el-input v-model="form.fault_reason" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="维修方法" required>
              <el-input v-model="form.repair_method" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="完成时间" required>
              <el-date-picker v-model="form.repair_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Tools, Search, Document, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applyCustomerResults, mergeSelectedCustomer } from '../../utils/customerOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const isBatch = computed(() => route.query.batch === '1')
const isKnowledge = computed(() => route.query.knowledge === '1')
const pageTitle = computed(() => isBatch.value ? '批量登记' : (isKnowledge.value ? '维修知识库搜索' : (isEdit.value ? '编辑维修记录' : '新增维修记录')))
const saving = ref(false)
const batchSaving = ref(false)
const formRef = ref()
const todayStr = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const form = reactive({
  id: null, customer: null, service: null, productcategory_id: null, product_id: null,
  productcategory_name: '', product_model: '',
  fault_text: '', fault_reason: '', repair_method: '',
  repair_date: todayStr(),
})
const customers = ref([])
const services = ref([])

const serviceLabel = (s) => {
  const parts = [s.service_number, s.productcategory__name, s.product__model].filter(Boolean)
  return parts.join(' / ')
}

const batchCustomer = ref(null)
const batchDate = ref(todayStr())
const batchServices = ref([])
const batchLoading = ref(false)

const kbQuery = ref('')
const kbData = ref({})

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/servicedetail/customers/', { params: { q: q || '' } })
    customers.value = applyCustomerResults(data, form.customer, customers.value)
  } catch {}
}

const onCustomerChange = async (cid) => {
  form.service = null
  services.value = []
  try {
    services.value = await request.get('/servicedetail/services/', { params: { customer_id: cid } })
  } catch {}
}

const onServiceChange = (val) => {
  const s = services.value.find(i => i.id === val)
  form.productcategory_id = s?.productcategory_id ?? null
  form.product_id = s?.product_id ?? null
  form.productcategory_name = s?.productcategory__name || ''
  form.product_model = s?.product__model || ''
}

const loadData = async () => {
  if (isBatch.value || isKnowledge.value) {
    await searchCustomers('')
    return
  }
  if (!isEdit.value) {
    await searchCustomers('')
    return
  }
  try {
    const data = await request.get(`/servicedetail/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, customer: data.customer || null, service: data.service || null,
      productcategory_id: data.productcategory || null, productcategory_name: data.productcategory_name || '',
      product_id: data.product || null, product_model: data.product_model || '',
      fault_text: data.fault_text || '', fault_reason: data.fault_reason || '',
      repair_method: data.repair_method || '', repair_date: data.repair_date || '',
    })
    customers.value = mergeSelectedCustomer(customers.value, data.customer, data.customer_name)
    services.value = [{
      id: data.service, service_number: data.service_number,
      productcategory_id: data.productcategory || null, product_id: data.product || null,
      productcategory__name: data.productcategory_name || '', product__model: data.product_model || '',
    }]
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.service) { ElMessage.warning('请选择维修编号'); return }
  if (!form.fault_text || !form.fault_reason || !form.repair_method) { ElMessage.warning('故障现象、故障原因、维修方法均不能为空'); return }
  if (!form.repair_date) { ElMessage.warning('请选择完成时间'); return }
  saving.value = true
  try {
    const payload = {
      customer: form.customer, service: form.service,
      productcategory: form.productcategory_id, product: form.product_id,
      fault_text: form.fault_text, fault_reason: form.fault_reason,
      repair_method: form.repair_method, repair_date: form.repair_date,
    }
    if (form.id) await request.put(`/servicedetail/${form.id}/`, payload)
    else await request.post('/servicedetail/', payload)
    ElMessage.success('保存成功')
    router.push('/servicedetail')
  } finally { saving.value = false }
}

const loadBatchServices = async () => {
  batchLoading.value = true
  try {
    const services = await request.get('/servicedetail/services/', { params: { customer_id: batchCustomer.value } })
    batchServices.value = services.map(s => ({ ...s, fault_text: '', fault_reason: '', repair_method: '' }))
  } finally { batchLoading.value = false }
}

const removeBatchRow = (index) => {
  batchServices.value.splice(index, 1)
}

const handleBatchSave = async () => {
  if (!batchCustomer.value) { ElMessage.warning('请选择客户名称'); return }
  if (!batchDate.value) { ElMessage.warning('请选择完成时间'); return }
  const items = batchServices.value.filter(s => s.fault_text || s.fault_reason || s.repair_method)
  if (!items.length) { ElMessage.warning('该项目暂无待维修产品'); return }
  batchSaving.value = true
  try {
    await request.post('/servicedetail/batch/', {
      customer: batchCustomer.value,
      repair_date: batchDate.value,
      items: items.map(s => ({
        service: s.id,
        productcategory: s.productcategory_id,
        product: s.product_id,
        fault_text: s.fault_text, fault_reason: s.fault_reason, repair_method: s.repair_method,
      })),
    })
    ElMessage.success('批量登记成功')
    router.push('/servicedetail')
  } finally { batchSaving.value = false }
}

const searchKnowledge = async () => {
  try {
    kbData.value = await request.get('/servicedetail/knowledge/', { params: { q: kbQuery.value } })
  } catch {}
}

const goBack = () => router.push('/servicedetail')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
.batch-hint { margin-top: 8px; color: #4a5a6a; font-size: 13px; }
.kb-search { margin-bottom: 12px; }
.kb-summary { margin-bottom: 12px; }
.kb-col-title { margin: 0 0 8px; color: #0078e0; font-size: 13px; font-weight: 700; }
.kb-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px; border-radius: 6px; background: #f4f6f9; margin-bottom: 6px; font-size: 13px; color: #1a2533; line-height: 1.5; }
.kb-case { border: 1px solid #eaf5ff; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; background: #fff; }
.kb-case-head { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; color: #1a2533; font-weight: 700; font-size: 13px; }
.kb-field { font-size: 13px; color: #1a2533; line-height: 1.6; margin-bottom: 5px; }
.kb-field b { color: #4a5a6a; }
.kb-meta { color: #8a97a5; font-size: 12px; }
</style>
