<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑型号' : '新增型号' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Box /></el-icon> 产品型号信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="产品名称" required>
              <el-select v-model="form.productcategory" filterable style="width:100%">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号" required>
              <el-input v-model="form.model" placeholder="如：KLD-500" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="仓库" required>
              <el-select v-model="form.warehouse" filterable style="width:100%">
                <el-option v-for="w in warehouses" :key="w.id" :label="w.name" :value="w.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="产品描述">
              <el-input v-model="form.description" type="textarea" :rows="2" placeholder="选填" />
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

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, productcategory: null, model: '', warehouse: null, description: '' })
const categories = ref([])
const warehouses = ref([])

const loadData = async () => {
  try {
    categories.value = (await request.get('/productcategory/?page_size=200')).results || []
    warehouses.value = (await request.get('/warehouse/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/product/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, productcategory: data.productcategory || null, model: data.model || '',
      warehouse: data.warehouse || null, description: data.description || '',
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.productcategory) { ElMessage.warning('请选择产品名称'); return }
  if (!form.model) { ElMessage.warning('请填写产品型号'); return }
  if (!form.warehouse) { ElMessage.warning('请选择仓库'); return }
  saving.value = true
  try {
    if (form.id) await request.put(`/product/${form.id}/`, form)
    else await request.post('/product/', form)
    ElMessage.success('保存成功')
    router.push('/product')
  } finally { saving.value = false }
}

const goBack = () => router.push('/product')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: #303133; }
.form-card { width: 100%; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
