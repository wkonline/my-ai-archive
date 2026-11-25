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
              <el-select v-model="form.customer" filterable remote :remote-method="searchCustomers" :loading="customerLoading" placeholder="输入客户名称搜索" style="width:100%" :disabled="isEdit" @change="onCustomerChange">
                <el-option v-for="c in customers" :key="c.id" :label="c.company_name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目编号" required>
              <el-select v-model="form.contract" filterable :loading="contractLoading" placeholder="选择项目编号" style="width:100%" :disabled="isEdit" @change="onContractChange">
                <el-option v-for="c in contractOptions" :key="c.id" :label="c.contract_number" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="发货日期" required>
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="收货人">
              <el-select v-if="contactOptions.length" v-model="selectedContact" placeholder="选择联系人或直接输入" clearable filterable allow-create default-first-option style="width:100%" @change="onContactSelect">
                <el-option v-for="(c, i) in contactOptions" :key="i" :label="contactLabel(c)" :value="i" />
              </el-select>
              <el-input v-else v-model="form.receiver" placeholder="收货人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.receiver_phone" placeholder="收货人联系电话" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="收货地址">
              <el-input v-model="form.receiver_address" placeholder="收货地址" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label=" ">
              <el-checkbox v-model="form.save_as_contact">同时保存为客户联系人</el-checkbox>
              <span class="tip">默认只记录在本张发货单上，不修改客户档案</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left"><el-icon><Goods /></el-icon> 发货产品</el-divider>
        <div v-if="!form.contract" class="empty-tip">请先选择项目编号，系统将自动带出该项目的全部产品</div>
        <el-table v-else :data="items" border size="small" empty-text="该项目下暂无生产计划产品">
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column prop="productcategory" label="产品名称" min-width="160" show-overflow-tooltip />
          <el-table-column prop="product" label="产品型号" min-width="140" show-overflow-tooltip />
          <el-table-column prop="quantity" label="计划数量" width="95" align="center" />
          <el-table-column prop="delivered" label="已发数量" width="95" align="center" />
          <el-table-column prop="remaining" label="剩余数量" width="95" align="center" />
          <el-table-column label="本次发货数量" width="150" align="center">
            <template #default="{ row }">
              <el-input-number v-model="row.send" :min="0" :max="row.maxSend ?? row.remaining" size="small" controls-position="right" style="width:110px" :disabled="(row.maxSend ?? row.remaining) <= 0" />
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" width="70" align="center" />
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.remaining <= 0" type="success" size="small">已发完</el-tag>
              <el-tag v-else-if="row.delivered > 0" type="warning" size="small">部分发货</el-tag>
              <el-tag v-else type="info" size="small">待发货</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="form.contract && items.length" class="sum-row">
          本次合计发货：<span class="sum-num">{{ totalSend }}</span>
        </div>
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
import { Van, Goods } from '@element-plus/icons-vue'
import request from '../../api/request'
import { applySearchResults } from '../../utils/dropdownOptions'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  id: null, customer: null, contract: null, date: '',
  receiver: '', receiver_phone: '', receiver_address: '', save_as_contact: false,
})
const customers = ref([])
const customerLoading = ref(false)
const contractOptions = ref([])
const contractLoading = ref(false)
const contacts = ref([])
const items = ref([])
const selectedContact = ref(null)
const editingPlanId = ref(null)
const editingQuantity = ref(0)

const totalSend = computed(() => items.value.reduce((sum, r) => sum + (Number(r.send) || 0), 0))

// 编辑态若原收货人已不在联系人表中，补一个「当前」选项，避免下拉框显示空值
const contactOptions = computed(() => {
  const list = [...contacts.value]
  if (form.receiver && !list.some(c => c.name === form.receiver)) {
    list.unshift({ name: form.receiver, phone: form.receiver_phone, title: '', _current: true })
  }
  return list
})

const contactLabel = (c) => {
  const base = c.phone ? `${c.name} ${c.phone}` : c.name
  const suffix = c._current ? '当前' : c.title
  return suffix ? `${base}（${suffix}）` : base
}

const searchCustomers = async (q = '') => {
  customerLoading.value = true
  try {
    const data = await request.get('/customer/', { params: { keyword: q, page_size: 200 }, silent: true })
    customers.value = applySearchResults(data.results || data, form.customer, customers.value)
  } catch {
    // 搜索失败不清空候选：已选客户必须留在列表里，否则下拉会退化成显示 id
  } finally {
    customerLoading.value = false
  }
}

const ensureCustomerOption = async (cid) => {
  if (!cid || customers.value.some(c => c.id === cid)) return
  try {
    const c = await request.get(`/customer/${cid}/`)
    if (c?.id) customers.value = [c, ...customers.value]
  } catch {}
}

const loadContracts = async (customerId) => {
  contractLoading.value = true
  try {
    const params = { page_size: 200 }
    if (customerId) params.customer = customerId
    contractOptions.value = (await request.get('/contract/', { params })).results || []
  } catch {
    contractOptions.value = []
  } finally {
    contractLoading.value = false
  }
}

const loadContractItems = async (contractId) => {
  if (!contractId) {
    items.value = []
    contacts.value = []
    return
  }
  try {
    const data = await request.get('/delivery/contract-items/', { params: { contract: contractId } })
    contacts.value = data.contacts || []
    let rows = (data.items || []).map(it => ({ ...it, send: 0 }))
    if (isEdit.value) {
      // 一条发货记录只对应一个产品，编辑态只保留该行，并把本次数量回填。
      // 可发上限 = 剩余量 + 本条记录原本占用的数量，否则改小再改大会被自己的量卡住。
      rows = rows.filter(it => it.plan === editingPlanId.value)
      if (rows.length) {
        rows[0].maxSend = rows[0].remaining + editingQuantity.value
        rows[0].send = editingQuantity.value
      }
    }
    items.value = rows
    if (data.customer && !form.customer) {
      form.customer = data.customer
      await ensureCustomerOption(data.customer)
    }
    if (!form.receiver && data.contact_person) form.receiver = data.contact_person
    if (!form.receiver_phone && data.phone) form.receiver_phone = data.phone
    if (!form.receiver_address && data.address) form.receiver_address = data.address
    if (isEdit.value) {
      // 回显当前收货人：优先匹配联系人姓名，匹配不上时由 contactOptions 补「当前」项
      const currentIndex = contactOptions.value.findIndex(c => c.name === form.receiver)
      selectedContact.value = currentIndex >= 0 ? currentIndex : null
    } else {
      const primaryIndex = contacts.value.findIndex(c => c.is_primary)
      if (contacts.value.length > 1 && primaryIndex >= 0) {
        selectedContact.value = primaryIndex
        onContactSelect(primaryIndex)
      }
    }
  } catch {
    items.value = []
  }
}

const onCustomerChange = async (cid) => {
  form.contract = null
  items.value = []
  contacts.value = []
  selectedContact.value = null
  await loadContracts(cid)
}

const onContractChange = async (contractId) => {
  await loadContractItems(contractId)
}

const onContactSelect = (index) => {
  const c = contactOptions.value[index]
  if (!c) return
  form.receiver = c.name || ''
  form.receiver_phone = c.phone || ''
}

const loadData = async () => {
  await searchCustomers('')
  if (!isEdit.value) {
    Object.assign(form, {
      id: null, customer: null, contract: null,
      date: new Date().toISOString().slice(0, 10),
      receiver: '', receiver_phone: '', receiver_address: '', save_as_contact: false,
    })
    await loadContracts(null)
    return
  }
  try {
    const data = await request.get(`/delivery/${route.params.id}/`)
    editingPlanId.value = data.contract || null
    editingQuantity.value = data.quantity || 0
    Object.assign(form, {
      id: data.id,
      customer: data.customer || null,
      contract: data.contract_id || null,
      date: data.date || '',
      receiver: data.contact_person || '',
      receiver_phone: data.phone || '',
      receiver_address: data.address || '',
      save_as_contact: false,
    })
    await ensureCustomerOption(data.customer)
    await loadContracts(data.customer)
    await loadContractItems(data.contract_id)
  } catch {}
}

const handleSave = async () => {
  if (!form.customer) { ElMessage.warning('请选择客户名称'); return }
  if (!form.contract) { ElMessage.warning('请选择项目编号'); return }
  if (!form.date) { ElMessage.warning('请选择发货日期'); return }

  const rows = items.value.filter(r => Number(r.send) > 0)
  if (!rows.length) { ElMessage.warning('请至少填写一行发货数量'); return }

  saving.value = true
  try {
    if (isEdit.value) {
      const row = rows[0]
      await request.put(`/delivery/${form.id}/`, {
        customer: form.customer,
        contract: row.plan,
        date: form.date,
        productcategory: row.productcategory,
        product: row.product,
        quantity: row.send,
        receiver: form.receiver,
        receiver_phone: form.receiver_phone,
        receiver_address: form.receiver_address,
        save_as_contact: form.save_as_contact,
      })
    } else {
      await request.post('/delivery/batch-create/', {
        customer: form.customer,
        contract: form.contract,
        date: form.date,
        receiver: form.receiver,
        receiver_phone: form.receiver_phone,
        receiver_address: form.receiver_address,
        save_as_contact: form.save_as_contact,
        items: rows.map(r => ({ plan: r.plan, quantity: r.send })),
      })
    }
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
.empty-tip { padding: 28px 0; text-align: center; color: #909399; background: #fafafa; border: 1px dashed #dcdfe6; border-radius: 4px; }
.sum-row { margin-top: 12px; text-align: right; font-size: 14px; color: #606266; }
.sum-num { font-size: 18px; font-weight: 700; color: var(--el-color-primary); }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
