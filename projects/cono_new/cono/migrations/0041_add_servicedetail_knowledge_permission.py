from django.db import migrations


NEW_PERMISSION = 'servicedetail_knowledge'
SOURCE_PERMISSION = 'servicedetail_list'


def grant_knowledge_permission(apps, schema_editor):
    """给已有 servicedetail_list 权限的角色补上知识库检索权限。"""
    AuthRole = apps.get_model('cono', 'AuthRole')
    AuthUserProfile = apps.get_model('cono', 'AuthUserProfile')

    for role in AuthRole.objects.all():
        permissions = list(role.permissions or [])
        if SOURCE_PERMISSION in permissions and NEW_PERMISSION not in permissions:
            permissions.append(NEW_PERMISSION)
            role.permissions = sorted(permissions)
            role.save(update_fields=['permissions'])

    for profile in AuthUserProfile.objects.all():
        extra = list(profile.extra_permissions or [])
        if SOURCE_PERMISSION in extra and NEW_PERMISSION not in extra:
            extra.append(NEW_PERMISSION)
            profile.extra_permissions = sorted(extra)
            profile.save(update_fields=['extra_permissions'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0040_rename_delivery_menu_title'),
    ]

    operations = [
        migrations.RunPython(grant_knowledge_permission, noop),
    ]
