<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">客户返回登记</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="120px" v-loading="loading">
        <el-divider content-position="left"><el-icon><Van /></el-icon> 待返回单据</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="流转编号" required>
              <el-select v-model="form.flow_out" filterable remote :remote-method="searchPending"
                         placeholder="搜索在客户处的流转编号" style="width:100%" @change="onFlowChange">
                <el-option v-for="f in pendingList" :key="f.id" :value="f.id" :label="f.flow_number">
                  <span>{{ f.flow_number }}</span>
                  <span class="option-sub">{{ f.serial_number }} / {{ f.customer_name }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际返回日期" required>
              <el-date-picker v-model="form.actual_return_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户名称">
              <el-input :model-value="currentFlow?.customer_name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="产品序列号">
              <el-input :model-value="currentFlow?.serial_number" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="产品型号">
              <el-input :model-value="currentFlow?.product_model" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="currentFlow?.situation" label="情况描述">
          <el-input :model-value="currentFlow.situation" type="textarea" :rows="2" readonly />
        </el-form-item>

        <el-divider content-position="left"><el-icon><Switch /></el-icon> 是否换板</el-divider>
        <el-radio-group v-model="form.is_board_swapped" @change="onSwapChange">
          <el-radio :value="false">未换板（客户退回原板）</el-radio>
          <el-radio :value="true">已换板（客户退回的是另一块板）</el-radio>
        </el-radio-group>

        <div v-if="form.is_board_swapped" class="swap-block">
          <el-alert
            type="warning" :closable="false" show-icon
            title="换板后原档案会标记为「已换板」并停用、置灰退役，永不再寄出；新档案走同一套送修判断。"
          />
          <el-row :gutter="16" class="swap-row">
            <el-col :span="12">
              <el-form-item label="新序列号" required>
                <el-input v-model="form.new_serial_number" placeholder="客户实际退回的电路板编号" maxlength="64" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="新产品名称">
                <el-select v-model="form.new_productcategory" filterable clearable placeholder="默认沿用原档案"
                           style="width:100%" @change="onNewCategoryChange">
                  <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="新产品型号">
                <el-select v-model="form.new_product" filterable clearable placeholder="默认沿用原档案" style="width:100%">
                  <el-option v-for="p in newProducts" :key="p.id" :label="p.model" :value="p.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="新档案经手人">
                <el-select v-model="form.new_handler" filterable clearable placeholder="默认当前操作人" style="width:100%">
                  <el-option v-for="u in users" :key="u.id" :label="u.name || u.username" :value="u.id" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <el-divider content-position="left"><el-icon><Tools /></el-icon> 返回后去向</el-divider>
        <el-radio-group v-model="form.result_status">
          <el-radio :value="1">直接回公司库存</el-radio>
          <el-radio :value="2">需要送修（转维修中）</el-radio>
        </el-radio-group>

        <el-alert
          v-if="form.result_status === 2"
          class="foot-note"
          type="success" :closable="false" show-icon
          :title="'保存后会自动生成一条售后服务单：客户「' + (currentFlow?.customer_name || '') +
                  '」，产品「' + (currentFlow?.productcategory_name || '') +
                  '」，型号「' + (currentFlow?.product_model || '') +
                  '」，电路板编号「' + serviceBoardSerial + '」，备注注明从售后流转过来。'"
        >
          <template #default>
            <div class="svc-preview">
              <span>客户：{{ currentFlow?.customer_name || '—' }}</span>
              <span>产品名称：{{ currentFlow?.productcategory_name || '—' }}</span>
              <span>产品型号：{{ currentFlow?.product_model || '—' }}</span>
              <span>电路板编号：{{ serviceBoardSerial || '—' }}</span>
              <span>备注：从售后流转过来</span>
            </div>
            <div class="svc-tip">
              维修完成后在「售后返件」登记返件，产品档案会自动标记为维修完成并回到公司库存。
            </div>
          </template>
        </el-alert>

        <el-alert
          v-else
          class="foot-note"
          type="info" :closable="false" show-icon
          title="选择「直接回公司库存」则不会生成售后服务单，档案保存后即可再次寄出。"
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
import { Van, Switch, Tools } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applySearchResults } from '../../utils/dropdownOptions'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)

const form = reactive({
  flow_out: null,
  actual_return_date: new Date().toISOString().slice(0, 10),
  is_board_swapped: false,
  result_status: 1,
  new_serial_number: '',
  new_productcategory: null,
  new_product: null,
  new_handler: null,
})

const pendingList = ref([])
const categories = ref([])
const allProducts = ref([])
const users = ref([])

const currentFlow = computed(() => pendingList.value.find(f => f.id === form.flow_out) || null)
const newProducts = computed(() => {
  if (!form.new_productcategory) return allProducts.value
  return allProducts.value.filter(p => p.productcategory === form.new_productcategory)
})

// 送修时售后服务单上的电路板编号：换板取新板，不换板取原板
const serviceBoardSerial = computed(() =>
  form.is_board_swapped ? (form.new_serial_number || '').trim() : (currentFlow.value?.serial_number || ''))

const searchPending = async (q) => {
  try {
    const data = await request.get('/flow-out/pending/', { params: { q: q || '' }, silent: true })
    pendingList.value = applySearchResults(data, form.flow_out, pendingList.value, 'flow_number')
  } catch { /* 保留上次结果 */ }
}

const onFlowChange = () => {
  // 切换单据时清掉换板信息，避免把上一单的新序列号带过来
  form.new_serial_number = ''
  form.new_productcategory = null
  form.new_product = null
}

const onSwapChange = (val) => {
  if (!val) {
    form.new_serial_number = ''
    form.new_productcategory = null
    form.new_product = null
    form.new_handler = null
  }
}

const onNewCategoryChange = () => { form.new_product = null }

const loadOptions = async () => {
  const [catData, prodData, userData] = await Promise.all([
    request.get('/productcategory/', { params: { page_size: 500 } }),
    request.get('/product/', { params: { page_size: 1000 } }),
    request.get('/user/options/'),
  ])
  categories.value = catData.results || catData
  allProducts.value = prodData.results || prodData
  users.value = userData.results || userData
}

const loadData = async () => {
  loading.value = true
  try {
    // 先落 query 预置的单据，searchPending 才能把它并进候选列表
    const preset = route.query.flow_out
    if (preset) form.flow_out = Number(preset)
    await Promise.all([searchPending(''), loadOptions()])
    if (form.flow_out && !pendingList.value.some(f => f.id === form.flow_out)) {
      const data = await request.get(`/flow-out/${form.flow_out}/`, { silent: true })
      pendingList.value = [{
        id: data.id,
        flow_number: data.flow_number,
        serial_number: data.archive_serial,
        customer_name: data.customer_name,
        product_model: data.product_model,
        productcategory_name: data.productcategory_name,
        situation: data.situation,
      }, ...pendingList.value]
    }
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!form.flow_out) { ElMessage.warning('请选择流转编号'); return }
  if (!form.actual_return_date) { ElMessage.warning('请选择实际返回日期'); return }
  if (form.is_board_swapped && !form.new_serial_number.trim()) {
    ElMessage.warning('换板时必须填写新序列号')
    return
  }

  const payload = {
    flow_out: form.flow_out,
    actual_return_date: form.actual_return_date,
    is_board_swapped: form.is_board_swapped,
    result_status: form.result_status,
  }
  if (form.is_board_swapped) {
    payload.new_serial_number = form.new_serial_number.trim()
    if (form.new_productcategory) payload.new_productcategory = form.new_productcategory
    if (form.new_product) payload.new_product = form.new_product
    if (form.new_handler) payload.new_handler = form.new_handler
  }

  saving.value = true
  try {
    await request.post('/flow-return/', payload)
    ElMessage.success('返回登记成功')
    router.push('/flow/return')
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

const goBack = () => router.push('/flow/return')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
.swap-block { margin-top: 12px; }
.swap-row { margin-top: 12px; }
.foot-note { margin-top: 12px; }
.svc-preview { display: flex; flex-wrap: wrap; gap: 4px 20px; color: var(--text-main); }
.svc-tip { margin-top: 6px; color: #8a96a3; font-size: 12px; }
.option-sub { float: right; color: #8a96a3; font-size: 12px; margin-left: 12px; }
</style>
