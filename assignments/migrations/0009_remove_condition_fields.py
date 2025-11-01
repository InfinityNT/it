# Migration to remove condition tracking fields from Assignment model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0008_delete_maintenancerequest'),
    ]

    operations = [
        # First, remove indexes that reference the condition fields
        migrations.RemoveIndex(
            model_name='assignment',
            name='assignments_conditi_0466e1_idx',  # condition_at_assignment index
        ),
        migrations.RemoveIndex(
            model_name='assignment',
            name='assignments_conditi_bd4987_idx',  # condition_at_return index
        ),
        # Now remove the fields
        migrations.RemoveField(
            model_name='assignment',
            name='condition_at_assignment',
        ),
        migrations.RemoveField(
            model_name='assignment',
            name='condition_at_return',
        ),
    ]
