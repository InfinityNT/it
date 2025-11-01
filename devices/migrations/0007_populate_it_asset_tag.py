from django.db import migrations, models


def populate_it_asset_tag(apps, schema_editor):
    """Populate IT Asset Tag for existing devices using MEX- + last 7 chars of serial"""
    Device = apps.get_model('devices', 'Device')
    
    counter = 1
    for device in Device.objects.filter(it_asset_tag__isnull=True):
        if device.serial_number and len(device.serial_number) >= 7:
            # Use MEX- + last 7 chars of serial number
            it_asset_tag = f"MEX-{device.serial_number[-7:]}"
        else:
            # Fallback for devices with short/missing serial numbers
            it_asset_tag = f"MEX-{counter:07d}"
            counter += 1
        
        # Ensure uniqueness
        original_tag = it_asset_tag
        unique_counter = 1
        while Device.objects.filter(it_asset_tag=it_asset_tag).exists():
            it_asset_tag = f"{original_tag}-{unique_counter}"
            unique_counter += 1
        
        device.it_asset_tag = it_asset_tag
        device.save()


def reverse_populate_it_asset_tag(apps, schema_editor):
    """Reverse migration - set IT Asset Tag to null"""
    Device = apps.get_model('devices', 'Device')
    Device.objects.all().update(it_asset_tag=None)


class Migration(migrations.Migration):
    dependencies = [
        ('devices', '0006_remove_device_devices_dev_buildin_c6619a_idx_and_more'),
    ]

    operations = [
        # Step 1: Ensure field is nullable (it was added as nullable in previous migration)
        # Step 2: Populate existing records
        migrations.RunPython(populate_it_asset_tag, reverse_populate_it_asset_tag),
        # Step 3: Make field non-nullable
        migrations.AlterField(
            model_name='device',
            name='it_asset_tag',
            field=models.CharField(help_text='IT department specific asset tag', max_length=50, unique=True),
        ),
    ]