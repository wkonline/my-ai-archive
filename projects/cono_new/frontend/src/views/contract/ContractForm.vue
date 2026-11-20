<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑合同' : '新增合同' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><CreditCard /></el-icon> 基础信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="合同日期" prop="date">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户名称" prop="customer">
              <el-select v-model="form.customer" filterable placeholder="输入客户名称搜索" style="width:100%" no-data-text="未找到匹配客户">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="合同编号" prop="contract_number">
              <el-input v-model="form.contract_number" placeholder="如：CN20261103" @input="checkContractNumber" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填，可记录该合同的补充说明、变更情况等信息。" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="contractNumberStatus" style="margin-top:-8px;margin-bottom:8px">
          <el-alert :title="contractNumberStatus" :type="contractNumberStatus.includes('可用') ? 'success' : 'error'" :closable="false" show-icon style="width:100%" />
        </el-form-item>

        <el-divider content-position="left"><el-icon><List /></el-icon> 产品明细</el-divider>

        <div class="product-toolbar">
          <span class="product-hint">支持新增、删除和自动计算金额</span>
          <el-button type="primary" size="small" @click="addProductRow">
            <el-icon><Plus /></el-icon>添加明细行
          </el-button>
        </div>

        <el-table :data="productRows" border size="small" class="product-table" empty-text="请点击「添加明细行」增加产品明细">
          <el-table-column label="序号" width="55" align="center">
            <template #default="{ $index }">{{ $index + 1 }}</template>
          </el-table-column>
          <el-table-column label="产品名称" min-width="160">
            <template #default="{ row }">
              <el-select v-model="row.category" placeholder="请选择产品名称" filterable @change="onCategoryChange(row)">
                <el-option v-for="c in productCategories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="产品型号" min-width="180">
            <template #default="{ row }">
              <el-select v-model="row.product" placeholder="请选择产品型号" filterable :disabled="!row.category">
                <el-option v-for="p in productsByCategory(row.category)" :key="p.id" :label="p.model" :value="p.id" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="服务类型" width="120">
            <template #default="{ row }">
              <el-select v-model="row.contract_type">
                <el-option label="销售服务" value="sale" />
                <el-option label="维修服务" value="repair" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="90">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="1" :controls="false" style="width:100%" @change="recalcRow(row)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.price" :min="0" :precision="2" :controls="false" style="width:100%" @change="recalcRow(row)" />
            </template>
          </el-table-column>
          <el-table-column label="金额" width="130">
            <template #default="{ row }">
              <span class="amount-cell">¥{{ (row.amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeProductRow($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="summary-strip">
          <span>已添加 <strong>{{ productRows.length }}</strong> 行明细</span>
          <span>产品总数量 <strong>{{ summaryQuantity }}</strong></span>
          <span class="summary-amount">合同金额合计 <strong>¥{{ summaryAmount.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</strong></span>
        </div>

        <el-form-item label="附件" style="margin-top:14px">
          <div class="attachment-area">
            <el-upload
              v-loading="uploading"
              class="upload-dragger"
              :action="uploadAction"
              :http-request="uploadFile"
              :on-success="onUploadSuccess"
              :on-error="onUploadError"
              :before-upload="beforeUpload"
              :show-file-list="false"
              drag
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击选择</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">支持单个文件上传，格式不限</div>
              </template>
            </el-upload>

            <!-- 已上传附件展示 -->
            <div v-if="form.attachment" class="uploaded-file">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-info">
                <div class="file-name">{{ attachmentName }}</div>
                <div class="file-size">{{ attachmentSize }}</div>
              </div>
              <el-link :href="`/media/${form.attachment}`" target="_blank" type="primary" :underline="false">
                <el-icon><Download /></el-icon>&nbsp;下载
              </el-link>
              <el-button type="danger" link size="small" @click="removeAttachment">
                <el-icon><Delete /></el-icon>&nbsp;删除
              </el-button>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存合同</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CreditCard, List, Plus, Delete, Document, Download, UploadFilled } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, date: new Date().toISOString().slice(0,10), customer: null, contract_number: '',
  quantity: 1, total_price: 0, remark: '', attachment: ''
})
const rules = {
  date: [{ required: true, message: '请选择合同日期', trigger: 'change' }],
  customer: [{ required: true, message: '请选择客户', trigger: 'change' }],
  contract_number: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
}

const customers = ref([])
const productCategories = ref([])
const productRows = ref([])
const contractNumberStatus = ref('')
const categoryProducts = ref({})

const emptyProductRow = () => ({
  id: null, category: null, product: null,
  contract_type: 'sale', quantity: 1, price: 0, amount: 0, description: ''
})

const summaryQuantity = computed(() =>
  productRows.value.reduce((s, r) => s + (Number(r.quantity) || 0), 0)
)
const summaryAmount = computed(() =>
  productRows.value.reduce((s, r) => s + (Number(r.amount) || 0), 0)
)

const productsByCategory = (categoryId) => {
  if (!categoryId) return []
  return categoryProducts.value[categoryId] || []
}

const recalcRow = (row) => {
  const qty = Number(row.quantity) || 0
  const price = Number(row.price) || 0
  row.amount = Math.round(qty * price * 100) / 100
}

const addProductRow = () => {
  productRows.value.push(emptyProductRow())
}

const removeProductRow = (index) => {
  if (productRows.value.length > 1) {
    productRows.value.splice(index, 1)
  } else {
    Object.assign(productRows.value[0], emptyProductRow())
  }
}

const onCategoryChange = (row) => {
  row.product = null
  loadProductsByCategory(row.category)
}

const loadProductsByCategory = async (categoryId) => {
  if (!categoryId) return
  try {
    const data = await request.get('/product/', { params: { productcategory: categoryId, page_size: 200 } })
    categoryProducts.value[categoryId] = data.results || data || []
  } catch { categoryProducts.value[categoryId] = [] }
}

// action 走 el-upload 的默认 ajax，需要完整路径；http-request 走 axios，baseURL 已是 /api
const uploadAction = '/api/contract/upload/'
const uploadEndpoint = '/contract/upload/'
const uploading = ref(false)
const uploadedSize = ref(0)

const attachmentName = computed(() => {
  if (!form.attachment) return ''
  return form.attachment.split(/[\\/]/).pop()
})
const attachmentSize = computed(() =>
  uploadedSize.value ? (uploadedSize.value / 1024).toFixed(1) + ' KB' : ''
)

const beforeUpload = (file) => {
  uploadedSize.value = file.size
  uploading.value = true
  return true
}

// 走 axios 而不是 el-upload 自带的 action：复用统一拦截器，access token 过期时能静默刷新后重放
const uploadFile = ({ file }) => {
  const fd = new FormData()
  fd.append('file', file)
  return request.post(uploadEndpoint, fd)
}

const defaultContractNumber = () => {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `CN${d.getFullYear()}W${mm}${dd}`
}

const loadData = async () => {
  try {
    const [custData, catData] = await Promise.all([
      request.get('/customer/', { params: { page_size: 2000 } }),
      request.get('/productcategory/', { params: { page_size: 200 } }),
    ])
    customers.value = custData.results || custData || []
    productCategories.value = catData.results || catData || []
  } catch {}

  if (isEdit.value) {
    try {
      const row = await request.get(`/contract/${route.params.id}/`)
      Object.assign(form, {
        id: row.id, date: row.date, customer: row.customer,
        contract_number: row.contract_number, remark: row.remark || '',
        attachment: row.attachment || '', quantity: row.quantity, total_price: row.total_price
      })
      uploadedSize.value = 0
      try {
        const data = await request.get(`/contract-product/?contract=${row.id}&page_size=200`)
        const items = (data.results || data || []).map(p => ({
          id: p.id, category: p.category, product: p.product,
          contract_type: p.contract_type, quantity: Number(p.quantity),
          price: Number(p.price), amount: Number(p.total_price),
          description: p.description || ''
        }))
        productRows.value = items.length ? items : [emptyProductRow()]
        items.forEach(p => { if (p.category) loadProductsByCategory(p.category) })
      } catch {
        productRows.value = [emptyProductRow()]
      }
    } catch {}
  } else {
    Object.assign(form, { id: null, date: new Date().toISOString().slice(0,10), customer: null, contract_number: defaultContractNumber(), quantity: 1, total_price: 0, remark: '', attachment: '' })
    productRows.value = [emptyProductRow()]
  }
}

const checkContractNumber = async () => {
  const num = (form.contract_number || '').trim()
  if (!num) { contractNumberStatus.value = ''; return }
  try {
    const params = { contract_number: num }
    if (form.id) params.exclude_id = form.id
    const data = await request.get('/contract/check-number/', { params })
    contractNumberStatus.value = data.message || ''
  } catch {
    contractNumberStatus.value = '合同编号检测失败，请稍后重试。'
  }
}

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    const validRows = productRows.value.filter(r => r.category && r.product)
    if (!validRows.length) {
      ElMessage.warning('请至少添加一条有效的产品明细')
      return
    }
    saving.value = true
    try {
      const payload = {
        date: form.date,
        customer: form.customer,
        contract_number: form.contract_number,
        remark: form.remark || '',
        attachment: form.attachment || '',
        products: validRows.map(r => ({
          category: r.category,
          product: r.product,
          contract_type: r.contract_type || 'sale',
          quantity: Number(r.quantity) || 0,
          price: Number(r.price) || 0,
          description: r.description || ''
        }))
      }
      if (form.id) {
        await request.put(`/contract/${form.id}/`, payload)
        ElMessage.success('更新成功')
      } else {
        await request.post('/contract/', payload)
        ElMessage.success('新增成功')
      }
      router.push('/contract')
    } finally { saving.value = false }
  })
}

const onUploadSuccess = (response) => {
  uploading.value = false
  form.attachment = response?.attachment || ''
  if (form.attachment) ElMessage.success('附件上传成功')
}
// 错误提示由 request.js 响应拦截器统一弹出，这里只重置状态
const onUploadError = () => {
  uploading.value = false
}
const removeAttachment = () => {
  form.attachment = ''
  uploadedSize.value = 0
}

const goBack = () => router.push('/contract')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.form-card :deep(.el-form) { width: 100%; }
.product-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.product-hint { font-size: 12px; color: #909399; }
.product-table { width: 100%; }
.product-table :deep(.el-select) { width: 100%; }
.product-table :deep(.el-input-number) { width: 100%; }
.amount-cell { font-weight: 600; color: #0078e0; }
.summary-strip {
  display: flex; align-items: center; justify-content: flex-end; gap: 24px;
  margin-top: 12px; padding: 10px 14px;
  border: 1px solid #e4e7ed; border-radius: 6px; background: #f4f6f9;
  font-size: 13px; color: #606266;
}
.summary-strip strong { color: #0078e0; font-size: 14px; }
.summary-amount strong { color: #f56c6c; font-size: 16px; }
.attachment-area { width: 100%; }
.attachment-area .upload-dragger {
  width: 100%;
}
.attachment-area .upload-dragger :deep(.el-upload) {
  width: 100%;
}
.attachment-area .upload-dragger :deep(.el-upload-dragger) {
  padding: 24px 16px;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  background: #fafafa;
  transition: all .2s;
}
.attachment-area .upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #0078e0;
  background: #eaf5ff;
}
.uploaded-file {
  display: flex; align-items: center; gap: 12px;
  margin-top: 12px; padding: 10px 14px;
  border: 1px solid #e4e7ed; border-radius: 8px;
  background: #f4f6f9;
}
.file-icon { font-size: 24px; color: #0078e0; }
.file-info { flex: 1; min-width: 0; }
.file-name { font-size: 13px; color: #303133; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { font-size: 12px; color: #909399; margin-top: 2px; }

.footer-actions {
  margin-top: 20px; padding-top: 16px;
  border-top: 1px solid #e4e7ed;
  display: flex; justify-content: flex-end; gap: 8px;
}
</style>
