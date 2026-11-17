"""API 权限校验：基于用户角色对应的 AuthRole.permissions。"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from api.core.models import AuthRole, AuthUserProfile


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
    role_key = getattr(user, 'role', 'servicer')
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
    """用户有效菜单 = 角色 menus（优先）+ 个人 menus（若 menu_customize）。"""
    role_key = getattr(user, 'role', 'servicer')
    profile = AuthUserProfile.objects.filter(user=user).first()
    if profile is not None and getattr(profile, 'menu_customize', False):
        return _normalize_menus(profile.menus)
    role = AuthRole.objects.filter(key=role_key).first()
    if role is not None:
        return _normalize_menus(role.menus)
    try:
        from django.conf import settings
        return _normalize_menus(settings.CONO_MENU.get(role_key, []))
    except Exception:
        return []


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
