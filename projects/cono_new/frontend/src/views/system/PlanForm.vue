<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑生产计划' : '新增生产计划' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="110px">
        <el-divider content-position="left"><el-icon><Calendar /></el-icon> 生产计划信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同编号" required>
              <el-select v-model="form.contract" filterable style="width:100%">
                <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_number" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备用编号">
              <el-input v-model="form.contract_reserve" placeholder="选填，临时计划编号" />
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
                <el-option v-for="p in filteredProducts" :key="p.id" :label="p.model" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数量" required>
              <el-input-number v-model="form.quantity" :min="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单位">
              <el-select v-model="form.unit" style="width:100%">
                <el-option :value="1" label="台" />
                <el-option :value="2" label="套" />
                <el-option :value="3" label="个" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生效日期">
              <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="交货日期">
              <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="详细配置">
              <el-input v-model="form.configuration" type="textarea" :rows="3" placeholder="请输入详细配置信息" />
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
import { Calendar } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, contract: null, contract_reserve: '', productcategory: null, product: null,
  quantity: 1, unit: 1, configuration: '', effective_date: '', delivery_date: '',
  completed: false,
})
const categories = ref([])
const products = ref([])
const contractOptions = ref([])

// 根据已选产品名称自动过滤型号
const filteredProducts = computed(() => {
  if (!form.productcategory) return products.value
  return products.value.filter(p => p.productcategory === form.productcategory)
})

// 用户手动切换产品名称时清空已选型号；编辑回填时不会触发 change，避免把型号清掉。
const onCategoryChange = () => { form.product = null }

// 编辑的数据可能不在下拉框已加载的 200 条里，单独补上，保证型号/合同能正常回显。
const ensureOption = async (list, id, endpoint) => {
  if (!id || list.value.some(item => item.id === id)) return
  try { list.value.push(await request.get(`/${endpoint}/${id}/`)) } catch {}
}

const loadData = async () => {
  try {
    categories.value = (await request.get('/productcategory/?page_size=200')).results || []
    products.value = (await request.get('/product/?page_size=200')).results || []
    contractOptions.value = (await request.get('/contract/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) {
    Object.assign(form, {
      id: null, contract: null, contract_reserve: '', productcategory: null, product: null,
      quantity: 1, unit: 1, configuration: '', effective_date: new Date().toISOString().slice(0, 10),
      delivery_date: '', completed: false,
    })
    return
  }
  try {
    const data = await request.get(`/plan/${route.params.id}/`)
    await Promise.all([
      ensureOption(products, data.product, 'product'),
      ensureOption(contractOptions, data.contract, 'contract'),
    ])
    Object.assign(form, {
      id: data.id, contract: data.contract || null, contract_reserve: data.contract_reserve || '',
      productcategory: data.productcategory || null, product: data.product || null,
      quantity: data.quantity ?? 1, unit: data.unit ?? 1, configuration: data.configuration || '',
      effective_date: data.effective_date || '', delivery_date: data.delivery_date || '',
      completed: !!data.completed,
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.contract) { ElMessage.warning('请选择合同编号'); return }
  if (!form.productcategory) { ElMessage.warning('请选择产品名称'); return }
  if (!form.product) { ElMessage.warning('请选择产品型号'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/plan/${form.id}/`, form)
    else await request.post('/plan/', form)
    ElMessage.success('保存成功')
    router.push('/plan')
  } finally { saving.value = false }
}

const goBack = () => router.push('/plan')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
