# Migration to remove condition field from Device model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0013_remove_financial_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='condition',
        ),
    ]
