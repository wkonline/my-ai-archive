<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ pageTitle }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Tools /></el-icon> 售后登记信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="维修编号">
              <el-input v-model="form.service_number" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers" style="width:100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
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
              <el-select v-model="form.product" filterable :disabled="!form.productcategory" :placeholder="form.productcategory ? '请选择产品型号' : '请先选择产品名称'" style="width:100%">
                <el-option v-for="p in productOptions" :key="p.id" :label="p.model" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品编号">
              <el-input v-model="form.product_number" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="质保情况">
              <el-select v-model="form.warranty" style="width:100%">
                <el-option :value="1" label="质保外" />
                <el-option :value="2" label="质保内" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="接收日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.description" type="textarea" :rows="2" />
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
import { Tools } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applyCustomerResults, mergeSelectedCustomer } from '../../utils/customerOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const isCopy = computed(() => route.query.copy === '1')
const saving = ref(false)
const formRef = ref()
const pageTitle = computed(() => isCopy.value ? '复制新增' : (isEdit.value ? '编辑售后' : '新增登记'))
const form = reactive({
  id: null, service_number: '', customer: null, productcategory: null, product: null,
  product_number: '', warranty: 1, date: '', description: '',
})
const customers = ref([])
const categories = ref([])
const productOptions = ref([])

// 选择产品名称后，按分类从后端拉取对应的产品型号，并清空上一次已选型号
const onCategoryChange = async (categoryId) => {
  form.product = null
  await loadProductOptions(categoryId)
}

const loadProductOptions = async (categoryId) => {
  if (!categoryId) { productOptions.value = []; return }
  try {
    const data = await request.get('/product/', { params: { productcategory: categoryId, page_size: 200 } })
    productOptions.value = data.results || data || []
  } catch { productOptions.value = [] }
}

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/service/customers/', { params: { q: q || '' } })
    customers.value = applyCustomerResults(data, form.customer, customers.value)
  } catch {}
}

const loadData = async () => {
  try {
    categories.value = (await request.get('/productcategory/?page_size=200', { silent: true })).results || []
    await searchCustomers('')
  } catch {}
  const id = route.params.id
  if (isEdit.value && !isCopy.value) {
    try {
      const data = await request.get(`/service/${id}/`)
      await loadProductOptions(data.productcategory)
      Object.assign(form, {
        id: data.id, service_number: data.service_number || '', customer: data.customer || null,
        productcategory: data.productcategory || null, product: data.product || null,
        product_number: data.product_number || '', warranty: data.warranty ?? 1,
        date: data.date || '', description: data.description || '',
      })
      if (data.customer_name) customers.value = mergeSelectedCustomer(customers.value, data.customer, data.customer_name)
    } catch {}
    return
  }
  try {
    const next = await request.get('/service/next-number/')
    Object.assign(form, {
      id: null, service_number: next.service_number || '', customer: null,
      productcategory: null, product: null, product_number: '',
      warranty: 1, date: new Date().toISOString().slice(0, 10), description: '',
    })
  } catch {}
  if (isCopy.value && isEdit.value) {
    try {
      const data = await request.get(`/service/${id}/`)
      await loadProductOptions(data.productcategory)
      Object.assign(form, {
        id: null, service_number: form.service_number, customer: data.customer || null,
        productcategory: data.productcategory || null, product: data.product || null,
        product_number: data.product_number || '', warranty: data.warranty ?? 1,
        date: new Date().toISOString().slice(0, 10), description: data.description || '',
      })
      if (data.customer_name) customers.value = mergeSelectedCustomer(customers.value, data.customer, data.customer_name)
    } catch {}
  }
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.productcategory) { ElMessage.warning('请选择产品名称'); return }
  if (!form.product) { ElMessage.warning('请选择产品型号'); return }
  if (!form.date) { ElMessage.warning('请选择接收日期'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/service/${form.id}/`, form)
    else await request.post('/service/', form)
    ElMessage.success('保存成功')
    router.push('/service')
  } finally { saving.value = false }
}

const goBack = () => router.push('/service')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
