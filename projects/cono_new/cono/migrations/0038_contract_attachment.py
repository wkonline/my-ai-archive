import cono.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cono', '0037_alter_collection_collection_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='attachment',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=cono.models.contract_attachment_path,
                verbose_name='合同附件',
            ),
        ),
    ]
