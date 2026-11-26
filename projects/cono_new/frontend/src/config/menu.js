// 侧边栏菜单与分组定义，供 AppLayout 与网站地图页共用，避免两处各自维护后漂移。
import {
  Document, Money, List, Calendar, TrendCharts, Upload, Postcard, Van,
  Tools, Setting, RefreshLeft, Switch, Files, Goods, OfficeBuilding, Box,
  User, InfoFilled, Clock, FolderOpened, Key, MapLocation,
} from '@element-plus/icons-vue'

// 分组顺序与标题，与后端 cono/tools/auth_profile.py: MENU_GROUP_ORDER 保持一致
export const MENU_GROUP_ORDER = ['业务单据', '生产交付', '基础资料', '售后服务', '系统管理']

// 菜单归属分组，与后端 MENU_GROUPS 保持一致
export const MENU_GROUPS = {
  业务单据: ['合同管理', '回款登记', '发票登记'],
  生产交付: ['生产计划', '派任务单', '产品铭牌', '发货信息', '资料上传'],
  基础资料: ['仓库管理', '部门管理', '用户管理', '客户管理', '产品分类', '产品管理'],
  售后服务: ['售后服务', '维修服务', '售后返件', '售后流转'],
  系统管理: ['应收应付', '数据备份', '操作日志', '公司信息', '账号密码', '权限管理', '网站地图'],
}

// 菜单入口所需权限码（与老版 MENU_PERMISSIONS 一致）
export const MENU_PERM = {
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
  '/flow/archive': ['flow_archive_list', 'flow_out_list', 'flow_return_list'],
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

// 侧边栏菜单定义（标题与路由权限一一对应）
export const SIDEBAR_ITEMS = [
  { path: '/contract', title: '合同管理', icon: Document },
  { path: '/invoice', title: '发票登记', icon: List },
  { path: '/collection', title: '回款登记', icon: Money },
  { path: '/accounts', title: '应收应付', icon: TrendCharts },
  { path: '/plan', title: '生产计划', icon: Calendar },
  { path: '/contract-file', title: '资料上传', icon: Upload },
  { path: '/task', title: '派任务单', icon: Calendar },
  { path: '/product-label', title: '产品铭牌', icon: Postcard },
  { path: '/delivery', title: '发货信息', icon: Van },
  { path: '/service', title: '售后服务', icon: Tools },
  { path: '/servicedetail', title: '维修服务', icon: Setting },
  { path: '/return-product', title: '售后返件', icon: RefreshLeft },
  { path: '/flow/archive', title: '售后流转', icon: Switch },
  { path: '/product-category', title: '产品分类', icon: Files },
  { path: '/product', title: '产品管理', icon: Goods, divider: true },
  { path: '/department', title: '部门管理', icon: OfficeBuilding },
  { path: '/warehouse', title: '仓库管理', icon: Box },
  { path: '/customer', title: '客户管理', icon: User },
  { path: '/company', title: '公司信息', icon: InfoFilled },
  { path: '/log', title: '操作日志', icon: Clock },
  { path: '/backup', title: '数据备份', icon: FolderOpened },
  { path: '/account-vault', title: '账号密码', icon: Key },
  { path: '/user', title: '用户管理', icon: User },
  { path: '/auth/role', title: '权限管理', icon: Setting },
]

// 每个菜单下可到达的子页面，供网站地图展示。列表页自身不在其中。
export const MENU_SUBPAGES = {
  '/contract': [
    { label: '合同详情', path: '/contract/:id' },
    { label: '合同产品展示', path: '/contract-product' },
  ],
  '/user': [
    { label: '用户权限', path: '/user/permission/:id' },
    { label: '我的资料', path: '/user/me' },
    { label: '修改资料', path: '/user/profile/edit' },
    { label: '修改密码', path: '/user/profile/password' },
  ],
  '/flow/archive': [
    { label: '寄给客户登记', path: '/flow/out' },
    { label: '客户返回登记', path: '/flow/return' },
  ],
}

// 不支持新增/编辑的页面，仅用于地图上的能力标注
export const READONLY_PAGES = ['/accounts', '/backup', '/company', '/log', '/sitemap']

// 常驻入口：不参与角色菜单勾选，登录后人人可见（与「首页」同等对待）。
// 网站地图只做导航概览，不含业务数据，因此不设权限码。
export const PINNED_ITEMS = [
  { path: '/sitemap', title: '网站地图', icon: MapLocation },
]
