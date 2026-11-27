import json

from django.conf import settings
from django.db import OperationalError
from collections import OrderedDict
from cono import models


def _try(value):
    try:
        return value()
    except (OperationalError, models.AuthRole.DoesNotExist, models.AuthUserProfile.DoesNotExist):
        return None


def all_permission_codes():
    codes = set()
    for perms in settings.CONO_PERMISSION.values():
        codes.update(perms)
    return sorted(codes)


# 内置角色：只有管理员和售后服务常驻，其余角色（含自定义角色）都可在权限管理页删除。
BUILTIN_ROLE_KEYS = ('admin', 'upkeeper')
# 兜底中文名：角色被删除后，仍属于该角色的用户还能显示出可读的名字。
ROLE_NAMES = dict(models.User.ROLE_CHOICES)
# 新用户默认角色 / 角色表为空时的兜底角色
DEFAULT_ROLE_KEY = 'upkeeper'


def is_builtin_role(role_key):
    return role_key in BUILTIN_ROLE_KEYS


def role_display_name(role_key):
    profile = get_role_profile(role_key)
    if profile is not None and profile.name:
        return profile.name
    return ROLE_NAMES.get(role_key, role_key)


def default_role_key():
    """新注册/新建用户的默认角色：内置的 upkeeper（售后服务）。

    不按「权限条数最少」动态挑选：条数会随管理员调整而变，而且 finance 之类角色
    条数少却握着金额数据，不适合当新用户的默认归属。先补内置角色，保证这个 key
    在 auth_role 表里一定存在，用户列表里不会出现指向空角色的账号。
    """
    ensure_default_roles()
    return DEFAULT_ROLE_KEY


PERMISSION_GROUPS = {
    '业务流程': [
        'contract_',
        'collection_',
        'invoice_',
        'get_collection_contracts',
        'get_collection_customers',
        'get_contract_amount',
        'get_invoice_contracts',
        'get_productcategory_product',
    ],
    '基础资料': [
        'customer_',
        'product_',
        'productcategory_',
        'warehouse_',
        'search_',
        'load_products',
    ],
    '生产与售后': [
        'plan_',
        'contract_file_',
        'electrical_file',
        'mechanical_file',
        'bill_file',
        'productlabel_',
        'delivery_',
        'task_',
        'service_',
        'servicedetail_',
        'return_product_',
        'get_servicedetail_services',
        'get_product_model',
        'get_return_product_services',
        'get_return_product_model',
        'flow_archive_',
        'flow_out_',
        'flow_return_',
    ],
    '统计分析': [
        'chart_',
        'highcharts',
    ],
    '系统管理': [
        'announcement_',
        'account_vault_',
        'user_',
        'department_',
        'company_',
        'get_log',
        'media',
        'backup_database',
        'restore_database',
        'auth_role_',
        'auth_user_permission',
    ],
    '接口权限': [
        'search_companys',
        'search_warehouses',
        'category_list',
        'get_category_list',
        'check_contract_number',
        'get_contract_amount',
        'upload_excel',
        'admin_',
        'print_plan',
    ],
}


PERMISSION_SPECIFIC_GROUPS = {
    'contract_file_': '生产与售后',
    'edit_contract_file': '生产与售后',
    'delete_contract_file': '生产与售后',
    'get_category_list': '生产与售后',
}


def permission_group(code):
    for prefix, group_name in PERMISSION_SPECIFIC_GROUPS.items():
        if code.startswith(prefix) or code == prefix:
            return group_name
    for group_name, prefixes in PERMISSION_GROUPS.items():
        for prefix in prefixes:
            if code.startswith(prefix) or code == prefix:
                return group_name
    return '其他权限'


PERMISSION_GROUP_ORDER = [
    '业务流程',
    '基础资料',
    '生产与售后',
    '统计分析',
    '系统管理',
    '接口权限',
    '其他权限',
]


PERMISSION_LABELS = {
    'department_list': '部门管理 - 列表查看',
    'department_add': '部门管理 - 新增部门',
    'department_edit': '部门管理 - 编辑部门',
    'department_delete': '部门管理 - 删除部门',
    'product_list': '产品型号 - 列表查看',
    'product_add': '产品型号 - 新增产品',
    'product_edit': '产品型号 - 编辑产品',
    'product_delete': '产品型号 - 删除产品',
    'productcategory_list': '产品名称 - 列表查看',
    'productcategory_add': '产品名称 - 新增产品名称',
    'productcategory_edit': '产品名称 - 编辑产品名称',
    'productcategory_delete': '产品名称 - 删除产品名称',
    'productcategory_multi': '产品名称 - 批量导入',
    'warehouse_list': '仓库管理 - 列表查看',
    'warehouse_add': '仓库管理 - 新增仓库',
    'warehouse_edit': '仓库管理 - 编辑仓库',
    'warehouse_delete': '仓库管理 - 删除仓库',
    'service_list': '售后服务 - 列表查看',
    'service_add': '售后服务 - 新增售后',
    'service_edit': '售后服务 - 编辑售后',
    'service_delete': '售后服务 - 删除售后',
    'service_download_excel': '售后服务 - 导出数据',
    'service_detail': '售后服务 - 查看详情',
    'servicedetail_list': '维修服务 - 列表查看',
    'servicedetail_add': '维修服务 - 新增维修记录',
    'servicedetail_batch_add': '维修服务 - 批量登记维修记录',
    'servicedetail_knowledge': '维修服务 - 知识库检索',
    'servicedetail_edit': '维修服务 - 编辑维修记录',
    'servicedetail_delete': '维修服务 - 删除维修记录',
    'servicedetail_download_excel': '维修服务 - 导出数据',
    'get_servicedetail_services': '维修服务 - 检索维修单',
    'get_product_model': '维修服务 - 读取产品型号',
    'contract_list': '合同管理 - 列表查看',
    'contract_create': '合同管理 - 新增合同',
    'contract_edit': '合同管理 - 编辑合同',
    'contract_delete': '合同管理 - 删除合同',
    'contract_product': '合同管理 - 查看合同明细',
    'contract_download_excel': '合同管理 - 导出合同',
    'contract_product_download_excel': '合同管理 - 导出合同产品',
    'contract_product_multi': '合同管理 - 批量导入合同产品',
    'customer_list': '客户管理 - 列表查看',
    'customer_add': '客户管理 - 新增客户',
    'customer_edit': '客户管理 - 编辑客户',
    'customer_delete': '客户管理 - 删除客户',
    'user_list': '用户管理 - 列表查看',
    'user_add': '用户管理 - 新增用户',
    'user_edit': '用户管理 - 编辑用户',
    'user_delete': '用户管理 - 删除用户',
    'user_reset': '用户管理 - 重置密码',
    'collection_list': '回款登记 - 列表查看',
    'collection_add': '回款登记 - 新增回款',
    'collection_create': '回款登记 - 新增回款二',
    'collection_edit': '回款登记 - 编辑回款',
    'collection_delete': '回款登记 - 删除回款',
    'collection_download_excel': '回款登记 - 导出数据',
    'get_collection_contracts': '回款登记 - 读取合同',
    'get_collection_customers': '回款登记 - 检索客户',
    'get_contract_amount': '回款登记 - 查询合同金额',
    'plan_list': '生产计划 - 列表查看',
    'plan_add': '生产计划 - 新增计划',
    'plan_edit': '生产计划 - 编辑计划',
    'plan_delete': '生产计划 - 删除计划',
    'plan_download_excel': '生产计划 - 导出数据',
    'contract_file_list': '资料上传 - 列表查看',
    'edit_contract_file': '资料上传 - 编辑文件',
    'delete_contract_file': '资料上传 - 删除文件',
    'electrical_file': '资料上传 - 上传电气图纸',
    'mechanical_file': '资料上传 - 上传机械图纸',
    'bill_file': '资料上传 - 上传装箱清单',
    'productlabel_list': '产品铭牌 - 列表查看',
    'productlabel_add': '产品铭牌 - 新增铭牌',
    'productlabel_edit': '产品铭牌 - 编辑铭牌',
    'productlabel_delete': '产品铭牌 - 删除铭牌',
    'delivery_list': '发货信息 - 列表查看',
    'delivery_add': '发货信息 - 新增发货',
    'delivery_edit': '发货信息 - 编辑发货',
    'delivery_delete': '发货信息 - 删除发货',
    'delivery_multi': '发货信息 - 批量导入',
    'delivery_download_excel': '发货信息 - 导出数据',
    'invoice_list': '发票登记 - 列表查看',
    'invoice_add': '发票登记 - 新增发票',
    'invoice_create': '发票登记 - 新增发票二',
    'invoice_edit': '发票登记 - 编辑发票',
    'invoice_delete': '发票登记 - 删除发票',
    'invoice_multi': '发票登记 - 批量导入',
    'get_invoice_contracts': '发票登记 - 读取合同',
    'chart_list': '应收应付 - 列表页面',
    'chart_bar': '应收应付 - 柱状图',
    'chart_bar2': '应收应付 - 历年业绩图',
    'chart_pie': '应收应付 - 饼图',
    'chart_line': '应收应付 - 折线图',
    'highcharts': '应收应付 - 图表示例',
    'return_product_list': '售后返件 - 列表查看',
    'return_product_add': '售后返件 - 新增返件',
    'return_product_batch_add': '售后返件 - 批量登记返件',
    'return_product_edit': '售后返件 - 编辑返件',
    'return_product_delete': '售后返件 - 删除返件',
    'return_product_download_excel': '售后返件 - 导出数据',
    'get_return_product_services': '售后返件 - 读取维修单',
    'get_return_product_model': '售后返件 - 读取产品型号',
    'flow_archive_list': '售后流转 - 产品档案列表',
    'flow_archive_add': '售后流转 - 新增产品档案',
    'flow_archive_edit': '售后流转 - 编辑产品档案',
    'flow_archive_stock': '售后流转 - 维修完成回库存',
    'flow_archive_download_excel': '售后流转 - 导出产品档案',
    'flow_out_list': '售后流转 - 寄出登记列表',
    'flow_out_add': '售后流转 - 新增寄出登记',
    'flow_out_edit': '售后流转 - 编辑寄出登记',
    'flow_out_delete': '售后流转 - 删除寄出登记',
    'flow_out_download_excel': '售后流转 - 导出寄出登记',
    'flow_return_list': '售后流转 - 返回登记列表',
    'flow_return_add': '售后流转 - 新增返回登记',
    'flow_return_edit': '售后流转 - 编辑返回登记',
    'flow_return_delete': '售后流转 - 删除返回登记',
    'flow_return_download_excel': '售后流转 - 导出返回登记',
    'task_list': '任务单 - 列表查看',
    'task_add': '任务单 - 新派任务',
    'task_edit': '任务单 - 编辑任务',
    'task_delete': '任务单 - 删除任务',
    'backup_database': '数据备份 - 数据库备份',
    'restore_database': '数据备份 - 数据库还原',
    'company_show': '公司信息 - 查看公司信息',
    'company_edit': '公司信息 - 编辑公司信息',
    'get_log': '操作日志 - 查看日志',
    'media': '媒体文件 - 访问媒体',
    'search_companys': '公共检索 - 搜索客户',
    'search_warehouses': '公共检索 - 搜索仓库',
    'load_products': '公共检索 - 读取产品',
    'get_category_list': '生产计划 - 读取产品名称',
    'get_productcategory_product': '合同新增 - 读取产品型号',
    'check_contract_number': '合同新增 - 检查合同编号',
    'upload_excel': '数据上传 - Excel 上传',
    'auth_role_list': '权限管理 - 角色列表',
    'auth_role_add': '权限管理 - 新建角色',
    'auth_role_edit': '权限管理 - 编辑角色',
    'auth_role_delete': '权限管理 - 删除角色',
    'auth_user_permission': '权限管理 - 用户权限配置',
    'account_vault_list': '账号密码 - 列表查看',
    'account_vault_add': '账号密码 - 新增记录',
    'account_vault_edit': '账号密码 - 编辑记录',
    'account_vault_delete': '账号密码 - 删除记录',
    'account_vault_password': '账号密码 - 查看/复制密码',
    'announcement_list': '公告管理 - 列表查看',
    'announcement_add': '公告管理 - 发布公告',
    'announcement_edit': '公告管理 - 编辑公告',
    'announcement_delete': '公告管理 - 删除公告',
}


def permission_label(code):
    return PERMISSION_LABELS.get(str(code), str(code).replace('_', ' ').title())


# 首页/菜单入口所需要的最小权限码。
# 键为 CONO_MENU 中的菜单标题，值为该入口可访问所需要的权限码集合，
# 只要用户拥有其中任意一个权限码，该入口就允许显示。
MENU_PERMISSIONS = {
    '合同管理': ('contract_list',),
    '回款登记': ('collection_list',),
    '发票登记': ('invoice_list',),
    '生产计划': ('plan_list',),
    '资料上传': ('contract_file_list',),
    '派任务单': ('task_list',),
    '产品铭牌': ('productlabel_list',),
    '发货信息': ('delivery_list',),
    '仓库管理': ('warehouse_list',),
    '部门管理': ('department_list',),
    '用户管理': ('user_list',),
    '客户管理': ('customer_list',),
    '产品分类': ('productcategory_list',),
    '产品管理': ('product_list',),
    '售后服务': ('service_list',),
    '维修服务': ('servicedetail_list',),
    '售后返件': ('return_product_list',),
    '售后流转': ('flow_archive_list', 'flow_out_list', 'flow_return_list'),
    '应收应付': ('chart_list', 'chart_bar', 'chart_bar2', 'chart_pie', 'chart_line', 'highcharts'),
    '数据备份': ('backup_database', 'restore_database'),
    '操作日志': ('get_log',),
    '公司信息': ('company_show',),
    '账号密码': ('account_vault_list',),
    '权限管理': ('auth_role_list', 'auth_user_permission'),
    '公告管理': ('announcement_list', 'announcement_add', 'announcement_edit'),
}


def menu_permissions(title):
    """返回菜单入口所需的权限码集合，未配置时返回空集合。"""
    return set(MENU_PERMISSIONS.get(str(title), ()))


def menu_allowed(title, permissions):
    """判断用户是否有权访问该菜单入口。

    未在 MENU_PERMISSIONS 中登记的入口按“放行”处理，避免新增菜单被误隐藏。
    """
    required = menu_permissions(title)
    if not required:
        return True
    return bool(required & set(permissions or ()))


def filter_allowed_menus(menus, permissions):
    """按权限过滤菜单列表，返回可访问的菜单项。"""
    return [item for item in (menus or []) if menu_allowed(item.get('title', ''), permissions)]


def menu_entry_url(item):
    """把 CONO_MENU 中的入口地址转换为可点击的列表页地址。

    CONO_MENU 里的 url 是模块前缀（如 /contract/），实际列表页多为前缀 + list/；
    但已有少部分配置直接写成完整地址（如 /database/backup/），需要原样保留。
    """
    from django.urls import resolve

    url = (item or {}).get('url', '/') or '/'
    if not url.endswith('/'):
        url += '/'
    if url.endswith('/list/') or url == '/':
        return url
    candidate = url + 'list/'
    try:
        resolve(candidate)
    except Exception:
        return url
    return candidate


def canonical_menus():
    menu_map = {}
    for items in settings.CONO_MENU.values():
        for item in items:
            menu_map[item['title']] = {'title': item['title'], 'url': item['url']}
    return list(menu_map.values())


MENU_GROUP_ORDER = [
    '业务单据',
    '生产交付',
    '基础资料',
    '售后服务',
    '系统管理',
]


MENU_GROUPS = {
    '业务单据': ['合同管理', '回款登记', '发票登记'],
    '生产交付': ['生产计划', '派任务单', '产品铭牌', '发货信息', '资料上传'],
    '基础资料': ['仓库管理', '部门管理', '用户管理', '客户管理', '产品分类', '产品管理'],
    '售后服务': ['售后服务', '维修服务', '售后返件', '售后流转'],
    '系统管理': ['应收应付', '数据备份', '操作日志', '公司信息', '账号密码', '权限管理', '公告管理'],
}


def grouped_permission_items():
    grouped = OrderedDict((name, []) for name in PERMISSION_GROUP_ORDER)
    for code in all_permission_codes():
        item = {'code': code, 'label': permission_label(code)}
        group_name = permission_group(code)
        if group_name not in grouped:
            grouped[group_name] = []
        grouped[group_name].append(item)
    return [{'name': name, 'items': items} for name, items in grouped.items() if items]


def grouped_menus():
    menus = canonical_menus()
    grouped = OrderedDict((name, []) for name in MENU_GROUP_ORDER)
    for item in menus:
        title = item.get('title', '')
        group_name = '其他权限'
        for name, prefixes in MENU_GROUPS.items():
            if any(title.startswith(prefix) for prefix in prefixes):
                group_name = name
                break
        if group_name not in grouped:
            grouped[group_name] = []
        grouped[group_name].append(item)
    return [{'name': name, 'items': items} for name, items in grouped.items() if items]


def sync_admin_role():
    """管理员角色始终与 settings 对齐：权限取全部权限码，菜单同步全部栏目。

    新增权限码/栏目只加在 settings 里，历史库里已有的 admin 记录不会自动更新，
    会出现「管理员进不了新功能、导航里也看不到新栏目」。管理员本来就放行全部
    （中间件与 API 都对 admin 直接 return），因此这里只对 admin 做强制对齐，
    其他角色（含 upkeeper）仍然尊重管理员在权限管理页里的勾选。
    """
    role = get_role_profile('admin')
    if role is None:
        return
    permissions = sorted(set(role.permissions or []) | set(all_permission_codes()))
    menus = settings.CONO_MENU.get('admin') or []
    if permissions == list(role.permissions or []) and menus == list(role.menus or []):
        return
    role.permissions = permissions
    role.menus = menus
    role.save(update_fields=['permissions', 'menus'])


def ensure_default_roles():
    """补齐内置角色（仅 admin/upkeeper）。

    按 key 逐个判断而不是整表 `exists()`：否则删掉某个内置角色后，只要表里还有
    其他角色就永远不会补回来。
    """
    existing = _try(lambda: set(models.AuthRole.objects.values_list('key', flat=True)))
    if existing is None:
        return
    for key in BUILTIN_ROLE_KEYS:
        if key in existing:
            continue
        models.AuthRole.objects.update_or_create(
            key=key,
            defaults={
                'name': ROLE_NAMES.get(key, key),
                'permissions': sorted(set(settings.CONO_PERMISSION.get(key, []) or [])),
                'menus': settings.CONO_MENU.get(key, []) or [],
            },
        )
    sync_admin_role()


def get_role_profile(role_key):
    return _try(lambda: models.AuthRole.objects.filter(key=role_key).first())


def get_role_permissions(role_key):
    """角色权限码集合：优先 auth_role 表，查不到时仅内置角色回退 settings。

    非内置角色（含已从 auth_role 删除的角色）不回退：settings.CONO_PERMISSION 里
    可能仍留有同名默认配置，继续回退会让「删除角色」无法真正收回权限。
    """
    profile = get_role_profile(role_key)
    if profile is not None:
        return set(profile.permissions or [])
    if not is_builtin_role(role_key):
        return set()
    return set(settings.CONO_PERMISSION.get(role_key, []))


def get_user_profile(user_id):
    return _try(lambda: models.AuthUserProfile.objects.filter(user_id=user_id).first())


def get_effective_permissions(user):
    profile = get_user_profile(user.id)
    permissions = get_role_permissions(user.role)
    if profile is not None:
        permissions.update(profile.extra_permissions or [])
        permissions.difference_update(profile.denied_permissions or [])
    return permissions


def get_session_permissions(role_key, user_id):
    profile = get_user_profile(user_id)
    permissions = get_role_permissions(role_key)
    if profile is not None:
        permissions.update(profile.extra_permissions or [])
        permissions.difference_update(profile.denied_permissions or [])
    return permissions


def get_effective_menus(user):
    # 管理员始终看全部栏目：新增栏目只改 settings 时，库里的 admin 记录可能还没同步，
    # 直接读 settings 才不会出现「新栏目看不到」。
    if getattr(user, 'role', '') == 'admin':
        return list(settings.CONO_MENU.get('admin', []) or [])
    profile = get_user_profile(user.id)
    if profile is not None and profile.menu_customize:
        raw = profile.menus or []
        return _ensure_list(raw)
    role_profile = get_role_profile(user.role)
    if role_profile is not None:
        raw = role_profile.menus or []
        return _ensure_list(raw)
    # 非内置角色没有 auth_role 记录 = 角色已被删除，不下发菜单（与权限的 fail-closed 一致）
    if not is_builtin_role(user.role):
        return []
    return settings.CONO_MENU.get(user.role, [])


def _ensure_list(raw):
    """确保 menus 字段返回的是列表，兼容历史数据中存储为 JSON 字符串的情况。"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []
