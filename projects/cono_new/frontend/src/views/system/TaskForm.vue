<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑任务单' : '新派任务单' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><Promotion /></el-icon> 任务单信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="下发日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目编号" required>
              <el-select v-model="form.contract" filterable style="width:100%" placeholder="请选择项目编号" @change="loadProducts">
                <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_number" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <p class="plan-tip">选择项目编号后，将自动列出该项目下所有产品项；下单数量默认等于计划数量，可修改。</p>
      </el-form>

      <!-- 产品下单明细 -->
      <el-divider content-position="left"><el-icon><Goods /></el-icon> 产品下单明细</el-divider>
      <el-table :data="form.rows" border size="small" class="product-table">
        <el-table-column label="产品名称" min-width="140">
          <template #default="{ row }"><el-input v-model="row.productcategory" readonly /></template>
        </el-table-column>
        <el-table-column label="产品型号" min-width="130">
          <template #default="{ row }"><el-input v-model="row.product" readonly /></template>
        </el-table-column>
        <el-table-column label="计划数量" width="80" align="center">
          <template #default="{ row }">{{ row.plan_quantity ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="下单数量" width="80">
          <template #default="{ row }">
            <el-input-number v-model="row.quantity" :min="1" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="操作" class-name="op-cell" width="100" align="center">
          <template #default="{ row, $index }">
            <el-button class="op-btn op-delete" size="small" @click="removeRow($index)"><el-icon><Delete /></el-icon>&nbsp;删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="form.rows.length === 0" description="请先选择项目编号" :image-size="60" />

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存任务单</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Promotion, Goods, Delete } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, contract: null, date: '', rows: [] })
const planOptions = ref([])
const assignedPlanIds = ref(new Set())

// 合同选项：只显示待生产且未派任务的计划
const contractOptions = computed(() => {
  const seen = new Map()
  for (const p of planOptions.value) {
    // 只显示待生产状态
    if (p.completed_status !== 1) continue
    // 跳过已派任务单的计划
    if (assignedPlanIds.value.has(p.id)) continue
    const cid = p.contract
    if (!cid || seen.has(cid)) continue
    seen.set(cid, { id: cid, contract_number: p.contract_number || p.contract_reserve || String(cid) })
  }
  return Array.from(seen.values())
})

// 选择项目编号后，列出该项目下所有产品项（计划数量自动填入下单数量）
const loadProducts = (contractId) => {
  form.rows = []
  if (!contractId) return
  const items = planOptions.value.filter(p => p.contract === contractId)
  form.rows = items.map(p => ({
    plan_id: p.id,
    productcategory: p.productcategory_name || '',
    product: p.product_model || '',
    plan_quantity: p.quantity ?? null,
    quantity: p.quantity ?? 1,
  }))
}

const removeRow = (idx) => form.rows.splice(idx, 1)

const loadData = async () => {
  try {
    const [planRes, taskRes] = await Promise.all([
      request.get('/plan/?page_size=2000', { silent: true }),
      request.get('/task/?page_size=2000'),
    ])
    planOptions.value = planRes.results || []
    // 收集已派任务单的计划ID
    assignedPlanIds.value = new Set(
      (taskRes.results || []).map(t => t.contract).filter(Boolean)
    )
  } catch {}
  if (!isEdit.value) {
    Object.assign(form, { id: null, contract: null, date: new Date().toISOString().slice(0, 10), rows: [] })
    return
  }
  try {
    const data = await request.get(`/task/${route.params.id}/`)
    Object.assign(form, {
      id: data.id,
      contract: data.contract || null,
      date: data.date || '',
      rows: [{
        plan_id: data.contract || null,
        productcategory: data.productcategory || '',
        product: data.product || '',
        plan_quantity: data.plan_quantity ?? null,
        quantity: data.quantity ?? 1,
      }],
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.contract) { ElMessage.warning('请选择项目编号'); return }
  if (form.rows.length === 0) { ElMessage.warning('该项目暂无可下单产品'); return }
  const valid = form.rows.filter(r => r.product)
  if (valid.length === 0) { ElMessage.warning('请至少保留一条有效产品'); return }
  saving.value = true
  try {
    if (form.id) {
      // 编辑：更新第一条，删除其余（老程序按行创建，编辑场景简单处理）
      await request.put(`/task/${form.id}/`, {
        contract: valid[0].plan_id, date: form.date,
        productcategory: valid[0].productcategory, product: valid[0].product,
        quantity: valid[0].quantity,
      })
    } else {
      for (const r of valid) {
        await request.post('/task/', {
          contract: r.plan_id, date: form.date,
          productcategory: r.productcategory, product: r.product,
          quantity: r.quantity,
        })
      }
    }
    ElMessage.success('保存成功')
    router.push('/task')
  } finally { saving.value = false }
}

const goBack = () => router.push('/task')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.plan-tip { margin: 4px 0 0; color: #8a97a5; font-size: 13px; }
.product-table { margin-top: 8px; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
