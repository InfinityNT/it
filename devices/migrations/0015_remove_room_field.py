# Migration to remove room field from Device model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0014_remove_condition_field'),
    ]

    operations = [
        # First, remove the index that references the room field
        migrations.RemoveIndex(
            model_name='device',
            name='devices_dev_locatio_bc454a_idx',  # location+room composite index
        ),
        # Now remove the room field
        migrations.RemoveField(
            model_name='device',
            name='room',
        ),
    ]
