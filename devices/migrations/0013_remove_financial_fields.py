# Generated migration to remove financial fields from Device model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0012_remove_it_asset_tag'),
    ]

    operations = [
        # First, remove indexes that reference the fields being dropped
        migrations.RemoveIndex(
            model_name='device',
            name='devices_dev_purchas_0816db_idx',  # purchase_date index
        ),
        migrations.RemoveIndex(
            model_name='device',
            name='devices_dev_warrant_74a51e_idx',  # warranty_expiry index
        ),
        # Now remove the fields
        migrations.RemoveField(
            model_name='device',
            name='purchase_date',
        ),
        migrations.RemoveField(
            model_name='device',
            name='purchase_price',
        ),
        migrations.RemoveField(
            model_name='device',
            name='warranty_expiry',
        ),
        migrations.RemoveField(
            model_name='device',
            name='vendor',
        ),
    ]
