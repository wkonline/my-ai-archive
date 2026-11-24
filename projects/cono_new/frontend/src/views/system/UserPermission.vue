<template>
  <div>
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">用户权限管理：{{ user.username }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" class="form-card" v-loading="loading">
      <el-form label-width="120px" class="base-form">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="角色">
              <el-select v-model="roleKey" style="width:100%">
                <el-option
                  v-for="r in roles"
                  :key="r.key"
                  :label="`${r.name}（${r.key}）`"
                  :value="r.key"
                  :disabled="r.deleted"
                />
              </el-select>
              <div v-if="roleDeleted" class="role-warning">
                该账号的角色「{{ user.role_display }}」已被删除，当前没有任何权限，请重新选择角色。
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="自定义顶部栏目">
              <el-select v-model="menuCustomize" style="width:100%">
                <el-option label="跟随角色栏目" :value="false" />
                <el-option label="仅使用下面勾选的栏目" :value="true" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="功能权限" name="perms">
          <el-alert
            type="info" :closable="false" show-icon class="tip"
            title="这里的「允许 / 禁止」是相对角色的差异：允许 = 角色没有但单独给他开；禁止 = 角色有但单独收走。"
          />
          <div class="group-grid">
            <div v-for="group in permGroups" :key="group.name" class="group-card">
              <div class="group-head">
                <span class="group-title">{{ group.name }}</span>
                <div class="group-actions">
                  <el-button size="small" @click="setGroup(group, 'allow')">全组允许</el-button>
                  <el-button size="small" @click="setGroup(group, 'clear')">清空该组</el-button>
                </div>
              </div>
              <div class="perm-list">
                <div v-for="item in group.items" :key="item.code" class="perm-row">
                  <div class="perm-name">
                    {{ item.label }}
                    <span class="permission-code">{{ item.code }}</span>
                  </div>
                  <el-checkbox :model-value="extraSet.has(item.code)" @change="v => setFlag(item.code, 'allow', v)">允许</el-checkbox>
                  <el-checkbox :model-value="deniedSet.has(item.code)" @change="v => setFlag(item.code, 'deny', v)">禁止</el-checkbox>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="顶部栏目" name="menus">
          <div class="group-grid">
            <div v-for="group in menuGroups" :key="group.name" class="group-card">
              <div class="group-head">
                <span class="group-title">{{ group.name }}</span>
                <div class="group-actions">
                  <el-button size="small" @click="setMenuGroup(group, true)">全选</el-button>
                  <el-button size="small" @click="setMenuGroup(group, false)">清空</el-button>
                </div>
              </div>
              <div class="menu-list">
                <el-checkbox
                  v-for="item in group.items" :key="item.title"
                  :model-value="menuSet.has(item.title)"
                  @change="v => setMenu(item.title, v)"
                >{{ item.title }}</el-checkbox>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <div class="footer-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存权限</el-button>
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
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('perms')

const user = reactive({ id: null, username: '', role: '', role_display: '' })
const roles = ref([])
const roleKey = ref('')
const roleDeleted = computed(() => {
  const current = roles.value.find((r) => r.key === roleKey.value)
  return !!current?.deleted
})
const menuCustomize = ref(false)
const permGroups = ref([])
const menuGroups = ref([])
const extraSet = reactive(new Set())
const deniedSet = reactive(new Set())
const menuSet = reactive(new Set())

const fillSet = (set, values) => {
  set.clear()
  ;(values || []).forEach(v => set.add(v))
}

const setFlag = (code, kind, checked) => {
  if (kind === 'allow') {
    checked ? extraSet.add(code) : extraSet.delete(code)
    if (checked) deniedSet.delete(code)
  } else {
    checked ? deniedSet.add(code) : deniedSet.delete(code)
    if (checked) extraSet.delete(code)
  }
}

const setGroup = (group, mode) => {
  group.items.forEach(item => {
    if (mode === 'allow') setFlag(item.code, 'allow', true)
    else { extraSet.delete(item.code); deniedSet.delete(item.code) }
  })
}

const setMenu = (title, checked) => { checked ? menuSet.add(title) : menuSet.delete(title) }
const setMenuGroup = (group, checked) => group.items.forEach(i => setMenu(i.title, checked))

const loadData = async () => {
  loading.value = true
  try {
    const data = await request.get(`/user/${route.params.id}/permission/`)
    Object.assign(user, data.user)
    roleKey.value = data.user.role
    roles.value = data.roles || []
    permGroups.value = data.permission_groups || []
    menuGroups.value = data.menu_groups || []
    menuCustomize.value = !!data.menu_customize
    fillSet(extraSet, data.extra_permissions)
    fillSet(deniedSet, data.denied_permissions)
    fillSet(menuSet, data.menus)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载权限失败')
  } finally { loading.value = false }
}

const handleSave = async () => {
  saving.value = true
  try {
    const payload = {
      role: roleKey.value,
      extra_permissions: Array.from(extraSet),
      denied_permissions: Array.from(deniedSet),
      menus: Array.from(menuSet),
      menu_customize: menuCustomize.value,
    }
    const data = await request.post(`/user/${user.id}/permission/`, payload)
    Object.assign(user, data.user)
    ElMessage.success('保存成功')
    router.push('/user')
  } catch (e) {
    const d = e?.response?.data
    const first = d && typeof d === 'object' ? Object.values(d).flat().find(v => typeof v === 'string') : null
    ElMessage.error(first || '保存失败')
  } finally { saving.value = false }
}

const goBack = () => router.push('/user')

onMounted(loadData)
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-title { font-size: 18px; font-weight: 700; color: var(--text-main); }
.form-card { width: 100%; }
.role-warning { margin-top: 6px; font-size: 12px; line-height: 1.5; color: #e6a23c; }
.base-form { margin-bottom: 4px; }
.tip { margin-bottom: 12px; }
.group-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.group-card { border: 1px solid #e4e7ed; border-radius: 8px; overflow: hidden; }
.group-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 10px 12px; background: #f7f9fa; border-bottom: 1px solid #e4e7ed; }
.group-title { font-size: 14px; font-weight: 600; color: var(--text-main); }
.group-actions { display: flex; gap: 6px; }
.perm-list { max-height: 320px; overflow-y: auto; padding: 6px 12px; }
.perm-row { display: grid; grid-template-columns: minmax(0, 1fr) 72px 72px; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px dashed #f0f2f5; }
.perm-row:last-child { border-bottom: 0; }
.perm-name { font-size: 13px; color: #4a5a6a; line-height: 1.4; }
.permission-code { display: block; font-size: 11px; color: #a8b3bd; }
.menu-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; padding: 10px 12px; max-height: 320px; overflow-y: auto; }
.footer-actions { margin-top: 18px; padding-top: 14px; border-top: 1px solid #e4e7ed; display: flex; justify-content: flex-end; gap: 8px; }
@media (max-width: 991px) { .group-grid { grid-template-columns: 1fr; } }
</style>
