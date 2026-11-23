from django.db import migrations


NEW_PERMISSIONS = [
    'flow_archive_list', 'flow_archive_add', 'flow_archive_edit',
    'flow_archive_stock', 'flow_archive_download_excel',
    'flow_out_list', 'flow_out_add', 'flow_out_edit', 'flow_out_delete',
    'flow_out_download_excel',
    'flow_return_list', 'flow_return_add', 'flow_return_edit', 'flow_return_delete',
    'flow_return_download_excel',
]

MENU_ITEM = {'title': '售后流转', 'url': '/flow/archive/'}

# 只给管理员和售后服务两个角色开权限；其余角色由管理员在权限管理页面手动勾选。
TARGET_ROLES = ('admin', 'upkeeper')


def _grant(permissions):
    merged = set(permissions or [])
    merged.update(NEW_PERMISSIONS)
    return sorted(merged)


def _grant_menus(menus):
    items = list(menus or [])
    if not any(isinstance(m, dict) and m.get('title') == MENU_ITEM['title'] for m in items):
        items.append(dict(MENU_ITEM))
    return items


def grant_flow_permissions(apps, schema_editor):
    AuthRole = apps.get_model('cono', 'AuthRole')
    AuthUserProfile = apps.get_model('cono', 'AuthUserProfile')

    for role in AuthRole.objects.filter(key__in=TARGET_ROLES):
        role.permissions = _grant(role.permissions)
        role.menus = _grant_menus(role.menus)
        role.save(update_fields=['permissions', 'menus'])

    # 个人覆盖记录：只处理属于目标角色的用户，避免给其他角色的人多开权限。
    profiles = AuthUserProfile.objects.select_related('user').filter(
        user__role__in=TARGET_ROLES)
    for profile in profiles:
        profile.extra_permissions = _grant(profile.extra_permissions)
        if profile.menu_customize:
            profile.menus = _grant_menus(profile.menus)
        profile.save(update_fields=['extra_permissions', 'menus'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0046_flowout_flowreturn_productarchive_and_more'),
    ]

    operations = [
        migrations.RunPython(grant_flow_permissions, noop),
    ]
