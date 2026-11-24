"""API 权限校验：基于用户角色对应的 AuthRole.permissions。"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from api.core.models import AuthRole, AuthUserProfile


def permission_catalog():
    """权限/菜单分组与中文名，供权限管理页面勾选。

    直接复用老版 cono/tools/auth_profile.py 的分组逻辑，避免两套分组规则不一致；
    老版模块不可用时退回 CONO_PERMISSION 平铺 + 简单分组。
    """
    try:
        from cono.tools.auth_profile import grouped_permission_items, grouped_menus
        return grouped_permission_items(), grouped_menus()
    except Exception:
        from django.conf import settings
        cono_perm = getattr(settings, 'CONO_PERMISSION', {}) or {}
        cono_menu = getattr(settings, 'CONO_MENU', {}) or {}
        codes = sorted({c for v in cono_perm.values() for c in (v or [])})
        groups = [{'name': '全部权限', 'items': [{'code': c, 'label': c} for c in codes]}]
        titles = {}
        for items in cono_menu.values():
            for item in (items or []):
                if item.get('title'):
                    titles[item['title']] = {'title': item['title'], 'url': item.get('url', '')}
        menus = [{'name': '顶部栏目', 'items': list(titles.values())}]
        return groups, menus


def _builtin_permissions(role_key):
    """从老版 settings.CONO_PERMISSION 读取内置角色默认权限。"""
    try:
        from django.conf import settings
        perms = getattr(settings, 'CONO_PERMISSION', {}) or {}
        return set(perms.get(role_key, []) or [])
    except Exception:
        return set()


def get_role_permissions(role_key):
    """获取角色权限码集合。

    - admin 返回 None（放行所有）
    - 优先读取 auth_role 表对应角色的 permissions
    - 无 auth_role 记录时回退到内置 CONO_PERMISSION 默认权限（保证旧角色仍生效）
    """
    if role_key == 'admin':
        return None  # admin 放行所有
    profile = AuthRole.objects.filter(key=role_key).first()
    if profile is not None:
        return set(profile.permissions or [])
    # 没有 auth_role 记录：使用内置默认权限
    return _builtin_permissions(role_key)


def get_effective_permissions(user):
    """用户有效权限 = 角色权限 + 个人 extra - 个人 denied。"""
    role_key = getattr(user, 'role', 'upkeeper')
    perms = get_role_permissions(role_key)
    if perms is None:
        return None  # admin
    profile = AuthUserProfile.objects.filter(user=user).first()
    if profile is not None:
        perms = set(perms)
        perms.update(profile.extra_permissions or [])
        perms.difference_update(profile.denied_permissions or [])
    return perms


def _normalize_menus(raw):
    """将 menus 统一为 [{title,url}] 列表，兼容 dict/str/混合存储。"""
    out = []
    for m in (raw or []):
        if isinstance(m, dict):
            t = m.get('title') or m.get('name')
            u = m.get('url') or m.get('path') or ''
            if t:
                out.append({'title': t, 'url': u})
        elif isinstance(m, str):
            out.append({'title': m, 'url': ''})
    return out


def get_effective_menus(user):
    """用户有效菜单 = 角色 menus（优先）+ 个人 menus（若 menu_customize）。

    结果再按权限过滤一次：CONO_MENU 里登记了权限码的入口，用户没有对应权限就不下发，
    避免侧边栏出现点击后报「无权限」的栏目（老版 /views/index.py 也是这么过滤的）。
    """
    role_key = getattr(user, 'role', 'upkeeper')
    if role_key == 'admin':
        # 管理员始终看全部栏目，避免库里 admin 记录未同步时看不到新栏目
        from django.conf import settings
        return _normalize_menus(settings.CONO_MENU.get('admin', []))
    profile = AuthUserProfile.objects.filter(user=user).first()
    if profile is not None and getattr(profile, 'menu_customize', False):
        menus = _normalize_menus(profile.menus)
    else:
        role = AuthRole.objects.filter(key=role_key).first()
        if role is not None:
            menus = _normalize_menus(role.menus)
        else:
            try:
                from django.conf import settings
                menus = _normalize_menus(settings.CONO_MENU.get(role_key, []))
            except Exception:
                return []
    return _filter_menus_by_permission(menus, get_effective_permissions(user))


def _filter_menus_by_permission(menus, permissions):
    """按 MENU_PERMISSIONS 过滤菜单；未登记权限码的入口保持可见。"""
    if permissions is None:
        return menus
    try:
        from cono.tools.auth_profile import filter_allowed_menus
    except Exception:
        return menus
    return filter_allowed_menus(menus, permissions)


# 标准 action -> 权限后缀映射（与老版 CONO_PERMISSION 的命名一致）。
# 例如 list -> *_list, create -> *_add, update/partial_update -> *_edit, destroy -> *_delete
ACTION_SUFFIX = {
    'list': 'list',
    'retrieve': 'list',
    'create': 'add',
    'update': 'edit',
    'partial_update': 'edit',
    'destroy': 'delete',
}


def _perm_code_for(view, action):
    """解析当前 action 需要的权限码集合。

    优先级：
    1. view.action_permission_codes 字典 {action: [codes]}（显式指定）
    2. 从基码推导 action 后缀（如 user_list -> user_edit）
       - create 同时接受 *_add 与 *_create
       - update 接受 *_edit
       - destroy 接受 *_delete
    3. view.permission_codes 作为兜底
    """
    action_map = getattr(view, 'action_permission_codes', None) or {}
    if action in action_map:
        code = action_map[action]
        return [code] if isinstance(code, str) else list(code)

    # 显式 permission_codes（如 contract_list）作为兜底/读取权限
    required = getattr(view, 'permission_codes', None)
    if not required:
        return None
    if isinstance(required, str):
        required = [required]

    suffix = ACTION_SUFFIX.get(action)
    if suffix:
        derived = []
        for base in required:
            base = str(base)
            if base.endswith('_list'):
                stem = base[:-len('_list')]
                if suffix == 'list':
                    derived.append(base)
                elif suffix == 'add':
                    # create 兼容 *_add 与 *_create（如 contract_add / contract_create）
                    derived.append(stem + '_add')
                    derived.append(stem + '_create')
                elif suffix == 'edit':
                    derived.append(stem + '_edit')
                elif suffix == 'delete':
                    derived.append(stem + '_delete')
            else:
                derived.append(base)
        # 去重，且保证与兜底不同（避免退化）
        derived = list(dict.fromkeys(derived))
        if derived and derived != required:
            return derived
    return required


class HasPermission(BasePermission):
    """基于角色权限的访问控制。

    view 可声明 permission_codes（字符串或列表）或
    action_permission_codes（{action: code}）。
    list/retrieve 校验 *_list，create 校验 *_add，
    update/partial_update 校验 *_edit，destroy 校验 *_delete。
    """

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'role', '') == 'admin':
            return True

        action = getattr(view, 'action', None)
        required = _perm_code_for(view, action)
        if not required:
            return True
        user_perms = get_effective_permissions(user)
        if user_perms is None:
            return True
        return any(code in user_perms for code in required)
