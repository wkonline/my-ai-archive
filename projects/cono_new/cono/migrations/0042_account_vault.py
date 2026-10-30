from django.db import migrations, models


NEW_PERMISSIONS = [
    'account_vault_list',
    'account_vault_add',
    'account_vault_edit',
    'account_vault_delete',
    'account_vault_password',
]
MENU_ITEM = {'title': '账号密码', 'url': '/account_vault/'}


def grant_account_vault(apps, schema_editor):
    """给管理员角色补上账号密码模块的权限和顶部栏目。"""
    AuthRole = apps.get_model('cono', 'AuthRole')
    AuthUserProfile = apps.get_model('cono', 'AuthUserProfile')

    for role in AuthRole.objects.filter(key='admin'):
        permissions = set(role.permissions or [])
        permissions.update(NEW_PERMISSIONS)
        role.permissions = sorted(permissions)
        menus = list(role.menus or [])
        if not any(item.get('title') == MENU_ITEM['title'] for item in menus):
            menus.append(MENU_ITEM)
        role.menus = menus
        role.save(update_fields=['permissions', 'menus'])

    for profile in AuthUserProfile.objects.all():
        if not profile.menu_customize:
            continue
        extra = set(profile.extra_permissions or [])
        extra.update(NEW_PERMISSIONS)
        profile.extra_permissions = sorted(extra)
        menus = list(profile.menus or [])
        if not any(item.get('title') == MENU_ITEM['title'] for item in menus):
            menus.append(MENU_ITEM)
        profile.menus = menus
        profile.save(update_fields=['extra_permissions', 'menus'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0041_add_servicedetail_knowledge_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountVault',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='是否删除')),
                ('category', models.CharField(blank=True, max_length=32, null=True, verbose_name='分类')),
                ('name', models.CharField(max_length=64, verbose_name='平台名称')),
                ('url', models.CharField(blank=True, max_length=255, null=True, verbose_name='网址')),
                ('account', models.CharField(blank=True, max_length=128, null=True, verbose_name='登录账号')),
                ('password', models.CharField(blank=True, max_length=128, null=True, verbose_name='登录密码')),
                ('remark', models.TextField(blank=True, null=True, verbose_name='备注')),
            ],
            options={
                'db_table': 'account_vault',
                'ordering': ['-id'],
            },
        ),
        migrations.RunPython(grant_account_vault, noop),
    ]
