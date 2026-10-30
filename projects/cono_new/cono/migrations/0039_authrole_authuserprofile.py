from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0038_contract_attachment'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=32, unique=True, verbose_name='角色标识')),
                ('name', models.CharField(max_length=64, verbose_name='角色名称')),
                ('permissions', models.JSONField(blank=True, default=list, verbose_name='权限编码')),
                ('menus', models.JSONField(blank=True, default=list, verbose_name='顶部栏目')),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'auth_role',
                'ordering': ['key'],
            },
        ),
        migrations.CreateModel(
            name='AuthUserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extra_permissions', models.JSONField(blank=True, default=list)),
                ('denied_permissions', models.JSONField(blank=True, default=list)),
                ('menus', models.JSONField(blank=True, default=list)),
                ('menu_customize', models.BooleanField(default=False)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_profile', to='cono.user', verbose_name='用户')),
            ],
            options={
                'db_table': 'auth_user_profile',
            },
        ),
    ]
