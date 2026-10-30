from django.db import migrations


OLD_TITLE = '入库发货'
NEW_TITLE = '发货信息'


def _normalize(menus):
    """去掉重复的入库发货栏目，并统一为发货信息。"""
    if not menus:
        return menus
    normalized = []
    seen = set()
    for item in menus:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        title = item.get('title')
        if title == OLD_TITLE:
            item = dict(item, title=NEW_TITLE)
            title = NEW_TITLE
        key = (title, item.get('url'))
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def merge_delivery_menu(apps, schema_editor):
    AuthRole = apps.get_model('cono', 'AuthRole')
    AuthUserProfile = apps.get_model('cono', 'AuthUserProfile')
    for model in (AuthRole, AuthUserProfile):
        for obj in model.objects.all():
            menus = _normalize(obj.menus)
            if menus != obj.menus:
                obj.menus = menus
                obj.save(update_fields=['menus'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0039_authrole_authuserprofile'),
    ]

    operations = [
        migrations.RunPython(merge_delivery_menu, noop),
    ]
