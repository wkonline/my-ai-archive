<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑产品档案' : '新增产品档案' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="110px" v-loading="loading">
        <el-divider content-position="left"><el-icon><Box /></el-icon> 产品信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品序列号" required>
              <el-input v-model="form.serial_number" placeholder="电路板编号，全局唯一" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入库日期" required>
              <el-date-picker v-model="form.stock_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称" required>
              <el-select v-model="form.productcategory" filterable style="width:100%" @change="onCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号" required>
              <el-select v-model="form.product" filterable style="width:100%">
                <el-option v-for="p in products" :key="p.id" :label="p.model" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="经手人" required>
              <el-select v-model="form.handler" filterable style="width:100%">
                <el-option v-for="u in users" :key="u.id" :label="u.name || u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left"><el-icon><Location /></el-icon> 当前状态</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="当前状态">
              <el-select v-model="form.status" style="width:100%" @change="onStatusChange">
                <el-option label="公司库存" :value="1" />
                <el-option label="客户试用中" :value="2" />
                <el-option label="维修中" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所在位置">
              <el-select v-model="form.location_type" style="width:100%">
                <el-option label="公司" :value="1" />
                <el-option label="客户" :value="2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="needCustomer">
            <el-form-item label="当前客户" required>
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers" style="width:100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="寄给客户请走「寄出登记」，返回请走「返回登记」；这里只用于建档和手工纠错。"
        />
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
import { Box, Location } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applySearchResults, mergeSelectedOption } from '../../utils/dropdownOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const saving = ref(false)
const formRef = ref()

const form = reactive({
  id: null,
  serial_number: '',
  productcategory: null,
  product: null,
  handler: null,
  stock_date: new Date().toISOString().slice(0, 10),
  status: 1,
  location_type: 1,
  customer: null,
})

const categories = ref([])
const products = ref([])
const allProducts = ref([])
const users = ref([])
const customers = ref([])

const needCustomer = computed(() => form.status === 2 || form.location_type === 2)

const onStatusChange = (v) => {
  form.location_type = v === 2 ? 2 : 1
  if (v === 1) form.customer = null
}

const onCategoryChange = () => {
  form.product = null
  products.value = allProducts.value.filter(p => p.productcategory === form.productcategory)
}

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/customer/', { params: { keyword: q || '', page_size: 200 }, silent: true })
    customers.value = applySearchResults(data.results || data, form.customer, customers.value)
  } catch { /* 保留上次结果 */ }
}

const loadOptions = async () => {
  const [catData, prodData, userData] = await Promise.all([
    request.get('/productcategory/', { params: { page_size: 500 } }),
    request.get('/product/', { params: { page_size: 1000 } }),
    request.get('/user/options/'),
  ])
  categories.value = catData.results || catData
  allProducts.value = prodData.results || prodData
  products.value = allProducts.value
  users.value = userData.results || userData
}

const loadData = async () => {
  loading.value = true
  try {
    await loadOptions()
    await searchCustomers('')
    if (!isEdit.value) return
    const data = await request.get(`/flow-archive/${route.params.id}/`)
    Object.assign(form, {
      id: data.id,
      serial_number: data.serial_number,
      productcategory: data.productcategory,
      product: data.product,
      handler: data.handler,
      stock_date: data.stock_date,
      status: data.status,
      location_type: data.location_type,
      customer: data.customer || null,
    })
    onCategoryChange()
    form.product = data.product
    if (data.customer) customers.value = mergeSelectedOption(customers.value, data.customer, data.customer_name)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!form.serial_number) { ElMessage.warning('请填写产品序列号'); return }
  if (!form.productcategory) { ElMessage.warning('请选择产品名称'); return }
  if (!form.product) { ElMessage.warning('请选择产品型号'); return }
  if (!form.handler) { ElMessage.warning('请选择经手人'); return }
  if (!form.stock_date) { ElMessage.warning('请选择入库日期'); return }
  if (needCustomer.value && !form.customer) { ElMessage.warning('请选择当前客户'); return }

  const payload = { ...form }
  delete payload.id
  if (!needCustomer.value) payload.customer = null

  saving.value = true
  try {
    if (form.id) await request.put(`/flow-archive/${form.id}/`, payload)
    else await request.post('/flow-archive/', payload)
    ElMessage.success('保存成功')
    router.push('/flow/archive')
  } catch (e) {
    const data = e?.response?.data
    const first = data && typeof data === 'object'
      ? Object.values(data).flat().find(v => typeof v === 'string')
      : null
    ElMessage.error(first || '保存失败')
  } finally {
    saving.value = false
  }
}

const goBack = () => router.push('/flow/archive')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
