<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑发货单' : '新增发货单' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Van /></el-icon> 发货信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-select v-model="form.customer" filterable style="width:100%">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目编号" required>
              <el-select v-model="form.contract" filterable style="width:100%">
                <el-option v-for="p in planOptions" :key="p.id" :label="(p.contract_number || p.contract_reserve || p.id) + ' - ' + (p.product_model || '')" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发货日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品名称">
              <el-input v-model="form.productcategory" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号">
              <el-input v-model="form.product" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="数量">
              <el-input-number v-model="form.quantity" :min="1" style="width:100%" />
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
import { Van } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, customer: null, contract: null, date: '', productcategory: '', product: '', quantity: 1 })
const customers = ref([])
const planOptions = ref([])

const loadData = async () => {
  try {
    customers.value = (await request.get('/customer/?page_size=200')).results || []
    planOptions.value = (await request.get('/plan/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) {
    Object.assign(form, { id: null, customer: null, contract: null, date: new Date().toISOString().slice(0, 10), productcategory: '', product: '', quantity: 1 })
    return
  }
  try {
    const data = await request.get(`/delivery/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, customer: data.customer || null, contract: data.contract || null,
      date: data.date || '', productcategory: data.productcategory || '',
      product: data.product || '', quantity: data.quantity ?? 1,
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.contract) { ElMessage.warning('请选择项目编号'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/delivery/${form.id}/`, form)
    else await request.post('/delivery/', form)
    ElMessage.success('保存成功')
    router.push('/delivery')
  } finally { saving.value = false }
}

const goBack = () => router.push('/delivery')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
