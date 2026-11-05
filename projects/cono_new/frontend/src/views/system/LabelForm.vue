<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑铭牌' : '新增铭牌' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="140px">
        <el-divider content-position="left"><el-icon><PriceTag /></el-icon> 产品铭牌信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品型号" required>
              <el-select v-model="form.product" filterable style="width:100%">
                <el-option v-for="p in products" :key="p.id" :label="p.model" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电源功率(kW)"><el-input v-model="form.power" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电源频率(kHz)"><el-input v-model="form.frequency" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供电容量(kVA)"><el-input v-model="form.sup_capacity" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供电电压(V)"><el-input v-model="form.sup_voltage" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供电频率(Hz)"><el-input v-model="form.sup_frequency" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供电电流(A)"><el-input v-model="form.sup_current" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高进水温度(°C)"><el-input v-model="form.max_in_temp" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大压力(MPa)"><el-input v-model="form.max_pressure" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最小流量(L/min)"><el-input v-model="form.min_flow" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最小压力(MPa)"><el-input v-model="form.min_pressure" /></el-form-item>
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
import { PriceTag } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, product: null, power: '', frequency: '', sup_capacity: '', sup_voltage: '',
  sup_frequency: '', sup_current: '', max_in_temp: '', max_pressure: '', min_flow: '', min_pressure: '',
})
const products = ref([])

const loadData = async () => {
  try {
    products.value = (await request.get('/product/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/product-label/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, product: data.product || null, power: data.power || '', frequency: data.frequency || '',
      sup_capacity: data.sup_capacity || '', sup_voltage: data.sup_voltage || '', sup_frequency: data.sup_frequency || '',
      sup_current: data.sup_current || '', max_in_temp: data.max_in_temp || '', max_pressure: data.max_pressure || '',
      min_flow: data.min_flow || '', min_pressure: data.min_pressure || '',
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.product) { ElMessage.warning('请选择产品型号'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/product-label/${form.id}/`, form)
    else await request.post('/product-label/', form)
    ElMessage.success('保存成功')
    router.push('/product-label')
  } finally { saving.value = false }
}

const goBack = () => router.push('/product-label')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
