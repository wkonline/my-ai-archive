<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑客户' : '新增客户' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-divider content-position="left"><el-icon><User /></el-icon> 客户信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户名称" required>
              <el-input v-model="form.company_name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input :model-value="primaryContactText" disabled placeholder="由下方主联系人自动带出" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务经理">
              <el-select v-model="form.saler" filterable style="width:100%">
                <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="地址">
              <el-input v-model="form.address" type="textarea" :rows="2" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left"><el-icon><UserFilled /></el-icon> 联系人</el-divider>
        <div class="contact-head">
          <span class="contact-tip">一个客户可以登记多个联系人，可留空；勾选「主」作为默认收货联系人。</span>
          <el-button class="btn-add-contact" size="small" @click="addContact">
            <el-icon><Plus /></el-icon>&nbsp;新增联系人
          </el-button>
        </div>
        <el-table :data="form.contacts" border size="small" empty-text="暂无联系人">
          <el-table-column label="主" width="56" align="center">
            <template #default="{ row }">
              <el-radio v-model="primaryIndex" :value="row._key" @change="onPrimaryChange">
                <span></span>
              </el-radio>
            </template>
          </el-table-column>
          <el-table-column label="姓名" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="联系人姓名" />
            </template>
          </el-table-column>
          <el-table-column label="电话" min-width="150">
            <template #default="{ row }">
              <el-input v-model="row.phone" placeholder="手机/座机" />
            </template>
          </el-table-column>
          <el-table-column label="职务" min-width="110">
            <template #default="{ row }">
              <el-input v-model="row.title" placeholder="选填" />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.remark" placeholder="选填" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="76" align="center">
            <template #default="{ $index }">
              <el-button class="op-btn op-delete" size="small" @click="removeContact($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
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
import { User, UserFilled, Plus } from '@element-plus/icons-vue'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: null, company_name: '', contact_person: '', phone: '', address: '', saler: null, contacts: [] })
const users = ref([])
let contactSeq = 0

const primaryIndex = computed({
  get: () => {
    const row = form.contacts.find(c => c.is_primary)
    return row ? row._key : null
  },
  set: (key) => {
    form.contacts.forEach(c => { c.is_primary = c._key === key })
  },
})

const primaryContactText = computed(() => {
  const row = form.contacts.find(c => c.is_primary)
  if (!row) return ''
  return row.phone ? `${row.name} ${row.phone}` : row.name
})

const addContact = () => {
  const item = { _key: ++contactSeq, name: '', phone: '', title: '', remark: '', is_primary: false }
  if (!form.contacts.length) item.is_primary = true
  form.contacts.push(item)
}

const removeContact = (index) => {
  const wasPrimary = form.contacts[index].is_primary
  form.contacts.splice(index, 1)
  if (wasPrimary && form.contacts.length) form.contacts[0].is_primary = true
}

const loadData = async () => {
  try {
    users.value = (await request.get('/user/?page_size=200')).results || []
  } catch {}
  if (!isEdit.value) return
  try {
    const data = await request.get(`/customer/${route.params.id}/`)
    Object.assign(form, {
      id: data.id, company_name: data.company_name || '', contact_person: data.contact_person || '',
      phone: data.phone || '', address: data.address || '', saler: data.saler || null,
      contacts: (data.contacts || []).map(c => ({
        _key: ++contactSeq, name: c.name || '', phone: c.phone || '',
        title: c.title || '', remark: c.remark || '', is_primary: !!c.is_primary,
      })),
    })
  } catch {}
}

const handleSave = async () => {
  if (!form.company_name) { ElMessage.warning('请填写客户名称'); return }
  const contacts = form.contacts
    .filter(c => (c.name || '').trim())
    .map(c => ({ name: c.name.trim(), phone: c.phone || '', title: c.title || '', remark: c.remark || '', is_primary: !!c.is_primary }))
  if (form.contacts.length && !contacts.length) { ElMessage.warning('联系人姓名不能为空'); return }
  const payload = {
    company_name: form.company_name, address: form.address,
    contacts,
  }
  // saler 不允许为 null，未选时不提交，交由模型默认值处理
  if (form.saler) payload.saler = form.saler
  saving.value = true
  try {
    if (form.id) await request.put(`/customer/${form.id}/`, payload)
    else await request.post('/customer/', payload)
    ElMessage.success('保存成功')
    router.push('/customer')
  } finally { saving.value = false }
}

const goBack = () => router.push('/customer')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.contact-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; gap: 12px; }
.contact-tip { font-size: 12px; color: var(--text-sub, #909399); }
.btn-add-contact { flex-shrink: 0; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
