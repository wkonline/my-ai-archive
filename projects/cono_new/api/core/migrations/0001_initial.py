"""api.core 没有自己的模型，全部来自 cono.models（见 api/core/models.py 的 import）。

历史版本这里重复定义了一整套与 cono/migrations 完全相同的表，后果是：
  * 新库 migrate 直接报 "table xxx already exists"；
  * makemigrations 会生成 DeleteModel 迁移，一旦 apply 就会 DROP 掉
    老版系统正在用的 contract / customer / invoice 等共享表。

因此保留三个空迁移：只为兼容已经记录过 core.0001~0003 的旧库，
不再产生任何数据库操作。表结构一律以 cono/migrations 为准。
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = []
