<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isBatch ? '批量登记返件' : (isEdit ? '编辑返件' : '新增返件') }}</span>
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
            <el-form-item label="返件日期" required>
              <el-date-picker v-model="batchDate" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <el-table :data="batchServices" stripe border size="small" v-loading="batchLoading">
        <el-table-column prop="service_number" label="维修编号" min-width="130" />
        <el-table-column prop="productcategory__name" label="产品名称" min-width="140" />
        <el-table-column prop="product__model" label="产品型号" min-width="130" />
        <el-table-column label="操作" class-name="op-cell" width="100" align="center">
          <template #default="{ $index }"><el-button type="danger" link size="small" @click="batchServices.splice($index,1)">删除</el-button></template>
        </el-table-column>
      </el-table>
      <div class="batch-hint">选择客户后自动带出可返件维修单，多行可单独删除。</div>
      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="success" :loading="batchSaving" @click="handleBatchSave">保存批量返件</el-button>
      </div>
    </el-card>

    <!-- 单个新增/编辑 -->
    <el-card v-else shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Box /></el-icon> 返件信息</el-divider>
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
            <el-form-item label="产品名称">
              <el-input :model-value="form.productcategory_name" disabled placeholder="选择维修编号后自动带出" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号">
              <el-input :model-value="form.product_model" disabled placeholder="选择维修编号后自动带出" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="返件日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
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
import { Box } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applyCustomerResults, mergeSelectedCustomer } from '../../utils/customerOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const isBatch = computed(() => route.query.batch === '1')
const saving = ref(false)
const batchSaving = ref(false)
const formRef = ref()
const todayStr = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const form = reactive({
  id: null, customer: null, service: null, productcategory_name: '', product_model: '',
  date: todayStr(),
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

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/return-product/customers/', { params: { q: q || '' } })
    customers.value = applyCustomerResults(data, form.customer, customers.value)
  } catch {}
}

const onCustomerChange = async (cid) => {
  form.service = null
  form.productcategory_name = ''
  form.product_model = ''
  services.value = []
  try {
    services.value = await request.get('/return-product/services/', { params: { customer_id: cid } })
  } catch {}
}

const onServiceChange = (val) => {
  const s = services.value.find(i => i.id === val)
  form.productcategory_name = s?.productcategory__name || ''
  form.product_model = s?.product__model || ''
}

const loadData = async () => {
  if (isBatch.value) {
    await searchCustomers('')
    return
  }
  if (!isEdit.value) {
    await searchCustomers('')
    return
  }
  try {
    const data = await request.get(`/return-product/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, customer: data.customer || null, service: data.service || null,
      productcategory_name: data.productcategory_name || '', product_model: data.product_model || '',
      date: data.date || '',
    })
    customers.value = mergeSelectedCustomer(customers.value, data.customer, data.customer_name)
    services.value = [{
      id: data.service,
      service_number: data.service_number,
      productcategory__name: data.productcategory_name,
      product__model: data.product_model,
    }]
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.service) { ElMessage.warning('请选择维修编号'); return }
  if (!form.date) { ElMessage.warning('请选择返件日期'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/return-product/${form.id}/`, form)
    else await request.post('/return-product/', form)
    ElMessage.success('保存成功')
    router.push('/return-product')
  } finally { saving.value = false }
}

const loadBatchServices = async () => {
  batchLoading.value = true
  try {
    batchServices.value = await request.get('/return-product/services/', { params: { customer_id: batchCustomer.value } })
  } finally { batchLoading.value = false }
}

const handleBatchSave = async () => {
  if (!batchCustomer.value) { ElMessage.warning('请选择客户名称'); return }
  if (!batchDate.value) { ElMessage.warning('请选择返件日期'); return }
  const serviceIds = batchServices.value.map(s => s.id)
  if (!serviceIds.length) { ElMessage.warning('该项目暂无可返件产品'); return }
  batchSaving.value = true
  try {
    await request.post('/return-product/batch/', {
      customer: batchCustomer.value,
      date: batchDate.value,
      service_ids: serviceIds,
    })
    ElMessage.success('批量返件成功')
    router.push('/return-product')
  } finally { batchSaving.value = false }
}

const goBack = () => router.push('/return-product')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
.batch-hint { margin-top: 8px; color: #4a5a6a; font-size: 13px; }
</style>
