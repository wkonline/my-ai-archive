<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑寄出登记' : '寄给客户登记' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="110px" v-loading="loading">
        <el-divider content-position="left"><el-icon><Box /></el-icon> 产品档案</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="流转编号" required>
              <el-input v-model="form.flow_number" readonly placeholder="保存时自动生成">
                <template #append>
                  <el-button @click="refreshNumber">重新生成</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品序列号" required>
              <el-select
                v-model="form.archive"
                filterable remote :remote-method="searchArchives"
                :disabled="isEdit"
                placeholder="搜索可寄出的序列号"
                style="width:100%"
              >
                <el-option v-for="a in archives" :key="a.id" :label="a.serial_number" :value="a.id">
                  <span>{{ a.serial_number }}</span>
                  <span class="option-sub">{{ a.productcategory_name }} / {{ a.product_model }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称">
              <el-input :model-value="currentArchive?.productcategory_name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号">
              <el-input :model-value="currentArchive?.product_model" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-alert
          v-if="!isEdit"
          type="info" :closable="false" show-icon
          title="下拉只列出「公司库存」的档案；已寄出或维修中的档案不会出现。"
        />

        <el-divider content-position="left"><el-icon><User /></el-icon> 客户信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers"
                         style="width:100%" @change="onCustomerChange">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户地址">
              <el-input v-model="form.customer_address" maxlength="128" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-select v-model="form.contact_name" filterable allow-create default-first-option
                         placeholder="选择或直接输入" style="width:100%">
                <el-option v-for="ct in contacts" :key="ct.id" :label="ct.name" :value="ct.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.contact_phone" maxlength="32" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left"><el-icon><Van /></el-icon> 寄出信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="寄出日期" required>
              <el-date-picker v-model="form.ship_date" type="date" value-format="YYYY-MM-DD"
                              style="width:100%" @change="refreshNumber" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计返回日期">
              <el-date-picker v-model="form.expected_return_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="快递公司">
              <el-input v-model="form.express_company" maxlength="64" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="快递单号">
              <el-input v-model="form.express_number" maxlength="64" />
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
import { Box, User, Van } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applySearchResults, mergeSelectedOption } from '../../utils/dropdownOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const loading = ref(false)
const saving = ref(false)

const form = reactive({
  id: null,
  flow_number: '',
  archive: null,
  customer: null,
  customer_address: '',
  contact_name: '',
  contact_phone: '',
  ship_date: new Date().toISOString().slice(0, 10),
  expected_return_date: null,
  express_company: '',
  express_number: '',
})

const archives = ref([])
const customers = ref([])
const contacts = ref([])

const currentArchive = computed(() => archives.value.find(a => a.id === form.archive) || null)

const searchArchives = async (q) => {
  try {
    const data = await request.get('/flow-archive/available/', { params: { q: q || '' } })
    archives.value = applySearchResults(data, form.archive, archives.value, 'serial_number')
  } catch { /* 保留上次结果 */ }
}

const searchCustomers = async (q) => {
  try {
    const data = await request.get('/customer/', { params: { keyword: q || '', page_size: 200 }, silent: true })
    customers.value = applySearchResults(data.results || data, form.customer, customers.value)
  } catch { /* 保留上次结果 */ }
}

const onCustomerChange = async (cid) => {
  contacts.value = []
  const picked = customers.value.find(c => c.id === cid)
  if (!picked) return
  // 地址与联系人作为快照落库，之后客户档案变更不影响这张单据
  form.customer_address = picked.address || ''
  form.contact_phone = picked.phone || ''
  contacts.value = picked.contacts || []
  const primary = contacts.value.find(c => c.is_primary) || contacts.value[0]
  if (primary) {
    form.contact_name = primary.name
    if (primary.phone) form.contact_phone = primary.phone
  }
}

const refreshNumber = async () => {
  if (isEdit.value) return
  try {
    const data = await request.get('/flow-out/next-number/', { params: { ship_date: form.ship_date } })
    form.flow_number = data.flow_number
  } catch { /* 保存时后端仍会校验编号 */ }
}

const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([searchArchives(''), searchCustomers('')])
    if (isEdit.value) {
      const data = await request.get(`/flow-out/${route.params.id}/`)
      Object.assign(form, {
        id: data.id,
        flow_number: data.flow_number,
        archive: data.archive,
        customer: data.customer,
        customer_address: data.customer_address || '',
        contact_name: data.contact_name || '',
        contact_phone: data.contact_phone || '',
        ship_date: data.ship_date,
        expected_return_date: data.expected_return_date || null,
        express_company: data.express_company || '',
        express_number: data.express_number || '',
      })
      const archiveOption = {
        id: data.archive,
        serial_number: data.archive_serial,
        productcategory_name: data.productcategory_name,
        product_model: data.product_model,
      }
      archives.value = [archiveOption, ...archives.value.filter(a => a.id !== data.archive)]
      customers.value = mergeSelectedOption(customers.value, data.customer, data.customer_name)
      return
    }
    await refreshNumber()
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!form.archive) { ElMessage.warning('请选择产品序列号'); return }
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.ship_date) { ElMessage.warning('请选择寄出日期'); return }

  const payload = { ...form }
  delete payload.id
  if (!payload.expected_return_date) delete payload.expected_return_date

  saving.value = true
  try {
    if (form.id) await request.put(`/flow-out/${form.id}/`, payload)
    else await request.post('/flow-out/', payload)
    ElMessage.success('保存成功')
    router.push('/flow/out')
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

const goBack = () => router.push('/flow/out')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
.option-sub { float: right; color: #8a96a3; font-size: 12px; margin-left: 12px; }
</style>
