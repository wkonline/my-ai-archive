import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/Login.vue'),
  },
  {
    path: '/',
    component: () => import('../views/layout/AppLayout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页' } },
      { path: 'contract', name: 'Contract', component: () => import('../views/contract/ContractList.vue'), meta: { title: '合同管理' } },
      { path: 'contract-product', name: 'ContractProduct', component: () => import('../views/contract/ContractProductList.vue'), meta: { title: '合同产品展示' } },
      { path: 'contract/new', name: 'ContractNew', component: () => import('../views/contract/ContractForm.vue'), meta: { title: '新增合同' } },
      { path: 'contract/edit/:id', name: 'ContractEdit', component: () => import('../views/contract/ContractForm.vue'), meta: { title: '编辑合同' } },
      { path: 'contract/:id', name: 'ContractDetail', component: () => import('../views/contract/ContractDetail.vue'), meta: { title: '合同详情' } },
      { path: 'service', name: 'Service', component: () => import('../views/service/ServiceList.vue'), meta: { title: '售后服务' } },
      { path: 'service/new', name: 'ServiceNew', component: () => import('../views/service/ServiceForm.vue'), meta: { title: '新增售后' } },
      { path: 'service/edit/:id', name: 'ServiceEdit', component: () => import('../views/service/ServiceForm.vue'), meta: { title: '编辑售后' } },
      { path: 'collection', name: 'Collection', component: () => import('../views/collection/CollectionList.vue'), meta: { title: '回款登记' } },
      { path: 'collection/new', name: 'CollectionNew', component: () => import('../views/collection/CollectionForm.vue'), meta: { title: '新增回款' } },
      { path: 'collection/edit/:id', name: 'CollectionEdit', component: () => import('../views/collection/CollectionForm.vue'), meta: { title: '编辑回款' } },
      { path: 'invoice', name: 'Invoice', component: () => import('../views/invoice/InvoiceList.vue'), meta: { title: '发票登记' } },
      { path: 'invoice/new', name: 'InvoiceNew', component: () => import('../views/invoice/InvoiceForm.vue'), meta: { title: '新增发票' } },
      { path: 'invoice/edit/:id', name: 'InvoiceEdit', component: () => import('../views/invoice/InvoiceForm.vue'), meta: { title: '编辑发票' } },
      { path: 'plan', name: 'Plan', component: () => import('../views/system/PlanList.vue'), meta: { title: '生产计划' } },
      { path: 'plan/new', name: 'PlanNew', component: () => import('../views/system/PlanForm.vue'), meta: { title: '新增生产计划' } },
      { path: 'plan/edit/:id', name: 'PlanEdit', component: () => import('../views/system/PlanForm.vue'), meta: { title: '编辑生产计划' } },
      { path: 'task', name: 'Task', component: () => import('../views/system/TaskList.vue'), meta: { title: '派任务单' } },
      { path: 'task/new', name: 'TaskNew', component: () => import('../views/system/TaskForm.vue'), meta: { title: '新派任务单' } },
      { path: 'task/edit/:id', name: 'TaskEdit', component: () => import('../views/system/TaskForm.vue'), meta: { title: '编辑任务单' } },
      { path: 'product-label', name: 'ProductLabel', component: () => import('../views/system/LabelList.vue'), meta: { title: '产品铭牌' } },
      { path: 'product-label/new', name: 'ProductLabelNew', component: () => import('../views/system/LabelForm.vue'), meta: { title: '新增产品铭牌' } },
      { path: 'product-label/edit/:id', name: 'ProductLabelEdit', component: () => import('../views/system/LabelForm.vue'), meta: { title: '编辑产品铭牌' } },
      { path: 'contract-file', name: 'ContractFile', component: () => import('../views/system/ContractFileView.vue'), meta: { title: '资料上传' } },
      { path: 'contract-file/new', name: 'ContractFileNew', component: () => import('../views/system/ContractFileForm.vue'), meta: { title: '新增资料' } },
      { path: 'contract-file/edit/:id', name: 'ContractFileEdit', component: () => import('../views/system/ContractFileForm.vue'), meta: { title: '编辑资料' } },
      { path: 'delivery', name: 'Delivery', component: () => import('../views/system/DeliveryList.vue'), meta: { title: '发货信息' } },
      { path: 'delivery/new', name: 'DeliveryNew', component: () => import('../views/system/DeliveryForm.vue'), meta: { title: '新增发货单' } },
      { path: 'delivery/edit/:id', name: 'DeliveryEdit', component: () => import('../views/system/DeliveryForm.vue'), meta: { title: '编辑发货单' } },
      { path: 'warehouse', name: 'Warehouse', component: () => import('../views/system/WarehouseList.vue'), meta: { title: '仓库管理' } },
      { path: 'warehouse/new', name: 'WarehouseNew', component: () => import('../views/system/WarehouseForm.vue'), meta: { title: '新增仓库' } },
      { path: 'warehouse/edit/:id', name: 'WarehouseEdit', component: () => import('../views/system/WarehouseForm.vue'), meta: { title: '编辑仓库' } },
      { path: 'department', name: 'Department', component: () => import('../views/system/DepartmentList.vue'), meta: { title: '部门管理' } },
      { path: 'department/new', name: 'DepartmentNew', component: () => import('../views/system/DepartmentForm.vue'), meta: { title: '新增部门' } },
      { path: 'department/edit/:id', name: 'DepartmentEdit', component: () => import('../views/system/DepartmentForm.vue'), meta: { title: '编辑部门' } },
      { path: 'user', name: 'User', component: () => import('../views/system/UserList.vue'), meta: { title: '用户管理' } },
      { path: 'user/new', name: 'UserNew', component: () => import('../views/system/UserForm.vue'), meta: { title: '新增用户' } },
      { path: 'user/edit/:id', name: 'UserEdit', component: () => import('../views/system/UserForm.vue'), meta: { title: '编辑用户' } },
      { path: 'user/me', name: 'UserProfile', component: () => import('../views/system/ProfileView.vue'), meta: { title: '我的资料' } },
      { path: 'user/profile/edit', name: 'ProfileEdit', component: () => import('../views/system/ProfileEdit.vue'), meta: { title: '修改资料' } },
      { path: 'user/profile/password', name: 'PasswordChange', component: () => import('../views/system/PasswordChange.vue'), meta: { title: '修改密码' } },
      { path: 'customer', name: 'Customer', component: () => import('../views/system/CustomerList.vue'), meta: { title: '客户管理' } },
      { path: 'customer/new', name: 'CustomerNew', component: () => import('../views/system/CustomerForm.vue'), meta: { title: '新增客户' } },
      { path: 'customer/edit/:id', name: 'CustomerEdit', component: () => import('../views/system/CustomerForm.vue'), meta: { title: '编辑客户' } },
      { path: 'product-category', name: 'ProductCategory', component: () => import('../views/system/CategoryList.vue'), meta: { title: '产品分类' } },
      { path: 'product-category/new', name: 'ProductCategoryNew', component: () => import('../views/system/CategoryForm.vue'), meta: { title: '新增产品分类' } },
      { path: 'product-category/edit/:id', name: 'ProductCategoryEdit', component: () => import('../views/system/CategoryForm.vue'), meta: { title: '编辑产品分类' } },
      { path: 'product', name: 'Product', component: () => import('../views/system/ProductList.vue'), meta: { title: '产品管理' } },
      { path: 'product/new', name: 'ProductNew', component: () => import('../views/system/ProductForm.vue'), meta: { title: '新增产品' } },
      { path: 'product/edit/:id', name: 'ProductEdit', component: () => import('../views/system/ProductForm.vue'), meta: { title: '编辑产品' } },
      { path: 'servicedetail', name: 'ServiceDetail', component: () => import('../views/service2/ServiceDetailView.vue'), meta: { title: '维修服务' } },
      { path: 'servicedetail/new', name: 'ServiceDetailNew', component: () => import('../views/service2/ServiceDetailForm.vue'), meta: { title: '新增维修记录' } },
      { path: 'servicedetail/edit/:id', name: 'ServiceDetailEdit', component: () => import('../views/service2/ServiceDetailForm.vue'), meta: { title: '编辑维修记录' } },
      { path: 'return-product', name: 'ReturnProduct', component: () => import('../views/service2/ReturnProductView.vue'), meta: { title: '售后返件' } },
      { path: 'return-product/new', name: 'ReturnProductNew', component: () => import('../views/service2/ReturnProductForm.vue'), meta: { title: '新增返件' } },
      { path: 'return-product/edit/:id', name: 'ReturnProductEdit', component: () => import('../views/service2/ReturnProductForm.vue'), meta: { title: '编辑返件' } },
      { path: 'accounts', name: 'Accounts', component: () => import('../views/system/ChartView.vue'), meta: { title: '应收应付' } },
      { path: 'chart', redirect: '/accounts' },
      { path: 'backup', name: 'Backup', component: () => import('../views/system/BackupView.vue'), meta: { title: '数据备份' } },
      { path: 'log', name: 'Log', component: () => import('../views/system/LogList.vue'), meta: { title: '操作日志' } },
      { path: 'company', name: 'Company', component: () => import('../views/system/CompanyView.vue'), meta: { title: '公司信息' } },
      { path: 'account-vault', name: 'AccountVault', component: () => import('../views/system/VaultList.vue'), meta: { title: '账号密码' } },
      { path: 'account-vault/new', name: 'AccountVaultNew', component: () => import('../views/system/VaultForm.vue'), meta: { title: '新增账号密码' } },
      { path: 'account-vault/edit/:id', name: 'AccountVaultEdit', component: () => import('../views/system/VaultForm.vue'), meta: { title: '编辑账号密码' } },
      { path: 'auth/role', name: 'Role', component: () => import('../views/system/RoleView.vue'), meta: { title: '权限管理' } },
      { path: 'auth/role/new', name: 'RoleNew', component: () => import('../views/system/RoleForm.vue'), meta: { title: '新增角色' } },
      { path: 'auth/role/edit/:id', name: 'RoleEdit', component: () => import('../views/system/RoleForm.vue'), meta: { title: '编辑角色' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function isTokenExpired() {
  const prefix = 'token_expiry_'
  const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage
  const expiry = storage.getItem(prefix + 'access_token')
  if (!expiry) return false
  return Date.now() >= Number(expiry)
}

const ROUTE_PERM = {
  '/contract': ['contract_list'],
  '/service': ['service_list'],
  '/collection': ['collection_list'],
  '/invoice': ['invoice_list'],
  '/plan': ['plan_list'],
  '/delivery': ['delivery_list'],
  '/customer': ['customer_list'],
  '/product-category': ['productcategory_list'],
  '/product': ['product_list'],
  '/servicedetail': ['servicedetail_list'],
  '/return-product': ['return_product_list'],
  '/task': ['task_list'],
  '/product-label': ['productlabel_list'],
  '/contract-file': ['contract_file_list'],
  '/warehouse': ['warehouse_list'],
  '/department': ['department_list'],
  '/user': ['user_list'],
  '/accounts': ['chart_list', 'chart_bar', 'chart_bar2', 'chart_pie', 'chart_line', 'highcharts'],
  '/backup': ['backup_database', 'restore_database'],
  '/log': ['get_log'],
  '/company': ['company_show'],
  '/account-vault': ['account_vault_list'],
  '/auth/role': ['auth_role_list', 'auth_user_permission'],
}
function routePermRequired(path) {
  return ROUTE_PERM[path] || ROUTE_PERM[path.replace(/\/new$/, '')] || ROUTE_PERM[path.replace(/\/edit\/\d+$/, '')] || null
}
router.beforeEach((to, from, next) => {
  if (import.meta.env.DEV && new URLSearchParams(window.location.search).get('dev')) {
    next()
    return
  }
  const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage
  const token = storage.getItem('access_token')
  if (to.path !== '/login' && (!token || isTokenExpired())) {
    if (isTokenExpired()) {
      for (const key of [
        'access_token',
        'refresh_token',
        'user_info',
        'user_permissions',
        'user_menus',
        'rememberDuration',
        'token_expiry_access_token',
        'token_expiry_refresh_token',
      ]) {
        localStorage.removeItem(key)
        sessionStorage.removeItem(key)
      }
    }
    next('/login')
    return
  }
  const required = routePermRequired(to.path)
  if (required) {
    const user = JSON.parse(storage.getItem('user_info') || 'null')
    const perms = JSON.parse(storage.getItem('user_permissions') || '[]')
    if ((user?.role || '') !== 'admin' && !required.some(c => perms.includes(c))) {
      next('/')
      return
    }
  }
  next()
})

export default router
