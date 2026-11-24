<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑角色' : '新增角色' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card">
      <el-form :model="form" ref="formRef" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="角色标识" required>
              <el-input v-model="form.key" :disabled="isEdit" placeholder="如：sales2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色名称" required>
              <el-input v-model="form.name" placeholder="如：销售组长" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-alert
        v-if="isAdminRole"
        class="admin-tip"
        type="warning"
        :closable="false"
        show-icon
        title="管理员角色固定拥有全部权限和栏目，这里只改中文名"
      />

      <el-tabs v-if="!isAdminRole" v-model="activeTab" class="role-tabs">
        <el-tab-pane label="菜单栏目" name="menus">
          <div class="perm-groups">
            <div v-for="group in menuGroupList" :key="group.name" class="perm-group">
              <div class="perm-group-title">
                <el-checkbox v-model="group._all" @change="toggleGroupMenus(group)">全选「{{ group.name }}」</el-checkbox>
              </div>
              <el-row :gutter="8">
                <el-col v-for="item in group.items" :key="item.title" :span="4">
                  <el-checkbox v-model="item._checked" @change="syncMenusFromFlags(group)">
                    {{ item.title }}
                  </el-checkbox>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="权限" name="perms">
          <div class="perm-groups">
            <div v-for="group in permGroupList" :key="group.name" class="perm-group">
              <div class="perm-group-title">
                <el-checkbox v-model="group._all" @change="toggleGroupPerms(group)">全选「{{ group.name }}」</el-checkbox>
                <span class="perm-count">{{ group._checkedCount }}/{{ group.items.length }}</span>
              </div>
              <el-row :gutter="6">
                <el-col v-for="code in group.items" :key="code" :span="6">
                  <el-checkbox v-model="permSet[code]" @change="updateGroupPermCount(group)">{{ permLabel(code) }}</el-checkbox>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

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
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const isAdminRole = ref(false)
const saving = ref(false)
const activeTab = ref('menus')
const options = ref({ role_names: {}, permission_groups: {}, menu_groups: {}, all_codes: [], permission_labels: {} })
const form = reactive({ id: null, key: '', name: '', menus: [], permissions: [] })
const permSet = reactive({})
const menuGroupList = ref([])
const permGroupList = ref([])

const permLabel = (code) => (options.value.permission_labels || {})[code] || code

const menuTitleSet = computed(() => {
  const s = new Set()
  ;(form.menus || []).forEach(m => s.add(m.title))
  return s
})

function buildMenuGroups() {
  const allMenus = new Map()
  Object.values(options.value.menu_groups || {}).forEach(list => {
    (list || []).forEach(m => { if (m && m.title && !allMenus.has(m.title)) allMenus.set(m.title, m) })
  })
  const menus = Array.from(allMenus.values())
  const groups = [
    { name: '销售合同', items: [] },
    { name: '生产交付', items: [] },
    { name: '售后服务', items: [] },
    { name: '基础资料', items: [] },
    { name: '系统管理', items: [] },
  ]
  const map = {
    '合同管理':'销售合同','回款登记':'销售合同','发票登记':'销售合同','应收应付':'销售合同',
    '生产计划':'生产交付','派任务单':'生产交付','资料上传':'生产交付','产品铭牌':'生产交付','发货信息':'生产交付',
    '售后服务':'售后服务','维修服务':'售后服务','售后返件':'售后服务','售后流转':'售后服务',
    '仓库管理':'基础资料','部门管理':'基础资料','用户管理':'基础资料','客户管理':'基础资料','产品分类':'基础资料','产品管理':'基础资料',
    '数据备份':'系统管理','操作日志':'系统管理','公司信息':'系统管理','账号密码':'系统管理','权限管理':'系统管理',
  }
  menus.forEach(m => {
    const g = map[m.title] || '基础资料'
    m._checked = menuTitleSet.value.has(m.title)
    groups.find(x => x.name === g).items.push(m)
  })
  groups.forEach(g => { g._all = g.items.every(i => i._checked); g._checkedCount = g.items.filter(i=>i._checked).length })
  menuGroupList.value = groups.filter(g => g.items.length)
}

function buildPermGroups() {
  const groups = []
  const allCodes = options.value.all_codes || []
  const prefixMap = [
    ['部门管理', c => c.startsWith('department_')],
    ['产品型号', c => c.startsWith('product_') && !c.startsWith('productlabel')],
    ['产品分类', c => c.startsWith('productcategory_')],
    ['仓库管理', c => c.startsWith('warehouse_')],
    ['售后服务', c => c.startsWith('service') && !c.startsWith('servicedetail')],
    ['维修服务', c => c.startsWith('servicedetail') || c.startsWith('get_servicedetail') || c.startsWith('get_product_model') || c.startsWith('get_productcategory_product')],
    ['合同管理', c => c.startsWith('contract') || c === 'get_contract_amount'],
    ['客户管理', c => c.startsWith('customer')],
    ['用户管理', c => c.startsWith('user_')],
    ['回款登记', c => c.startsWith('collection') || c.startsWith('get_collection')],
    ['发票登记', c => c.startsWith('invoice') || c.startsWith('get_invoice')],
    ['生产计划', c => c.startsWith('plan') || c === 'media' || c === 'print_plan'],
    ['资料上传', c => c.includes('contract_file') || c === 'electrical_file' || c === 'mechanical_file' || c === 'bill_file'],
    ['产品铭牌', c => c.startsWith('productlabel_')],
    ['发货信息', c => c.startsWith('delivery')],
    ['任务单', c => c.startsWith('task_')],
    ['售后返件', c => c.startsWith('return_product') || c.startsWith('get_return_product')],
    ['售后流转', c => c.startsWith('flow_archive_') || c.startsWith('flow_out_') || c.startsWith('flow_return_')],
    ['账号密码', c => c.startsWith('account_vault')],
    ['图表', c => c.startsWith('chart') || c === 'highcharts' || c === 'chart_list'],
    ['管理员', c => c.startsWith('admin_')],
    ['数据备份', c => c === 'backup_database' || c === 'restore_database'],
    ['公司信息', c => c.startsWith('company_')],
    ['操作日志', c => c === 'get_log'],
    ['权限管理', c => c.startsWith('auth_') || c === 'upload_excel' || c.startsWith('search_') || c.startsWith('load_') || c === 'get_category_list' || c === 'get_contract_amount'],
    ['其他', c => true],
  ]
  allCodes.forEach(code => { permSet[code] = (form.permissions || []).includes(code) })
  prefixMap.forEach(([name, test]) => {
    const items = allCodes.filter(code => test(code))
    if (items.length) groups.push({ name, items, _all: false, _checkedCount: 0 })
  })
  groups.forEach(g => {
    g._checkedCount = g.items.filter(c => permSet[c]).length
    g._all = g._checkedCount === g.items.length
  })
  permGroupList.value = groups
}

function toggleGroupMenus(group) {
  group.items.forEach(i => { i._checked = group._all })
  syncMenusFromFlags(group)
}
function syncMenusFromFlags(group) {
  group._all = group.items.every(i => i._checked)
  const titles = new Set()
  menuGroupList.value.forEach(g => g.items.forEach(i => { if (i._checked) titles.add(i.title) }))
  form.menus = Array.from(titles).map(t => menuTitleItem(t))
}
function menuTitleItem(title) {
  for (const g of menuGroupList.value) { const m = g.items.find(i => i.title === title); if (m) return m }
  return { title }
}
function updateGroupPermCount(group) {
  group._checkedCount = group.items.filter(c => permSet[c]).length
  group._all = group._checkedCount === group.items.length
}
function toggleGroupPerms(group) {
  group.items.forEach(c => { permSet[c] = group._all })
  updateGroupPermCount(group)
}

async function loadOptions() {
  const d = await request.get('/auth-role/permission-options/')
  options.value = d
}

const loadData = async () => {
  await loadOptions()
  if (isEdit.value) {
    try {
      const data = await request.get(`/auth-role/${route.params.id}/`)
      Object.assign(form, { id: data.id, key: data.key || '', name: data.name || '', menus: data.menus || [], permissions: data.permissions || [] })
      isAdminRole.value = data.key === 'admin'
    } catch {}
  }
  Object.keys(permSet).forEach(k => delete permSet[k])
  buildMenuGroups()
  buildPermGroups()
}

async function handleSave() {
  if (!form.key) { ElMessage.warning('请输入角色标识'); return }
  if (!form.name) { ElMessage.warning('请输入角色名称'); return }
  if (isAdminRole.value) {
    // 管理员的权限/栏目由后端按 settings 同步，提交也没用，只提交中文名
    saving.value = true
    try {
      await request.put(`/auth-role/${form.id}/`, { name: form.name })
      ElMessage.success('保存成功')
      router.push('/auth/role')
    } finally { saving.value = false }
    return
  }
  const perms = Object.keys(permSet).filter(c => permSet[c])
  form.permissions = perms
  saving.value = true
  try {
    const payload = { key: form.key, name: form.name, menus: form.menus, permissions: form.permissions }
    if (form.id) await request.put(`/auth-role/${form.id}/`, payload)
    else await request.post('/auth-role/', payload)
    ElMessage.success('保存成功')
    router.push('/auth/role')
  } finally { saving.value = false }
}

const goBack = () => router.push('/auth/role')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.role-tabs { margin-top: 8px; }
.admin-tip { margin-top: 8px; }
.perm-groups { max-height: 500px; overflow-y: auto; padding-right: 4px; }
.perm-group { margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed #ebeef5; }
.perm-group-title { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.perm-count { font-size: 12px; color: #909399; }
.footer-actions { margin-top: 20px; padding-top: 16px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
</style>
