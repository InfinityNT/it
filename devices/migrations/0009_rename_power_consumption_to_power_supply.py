from django.db import migrations


def rename_power_consumption_to_power_supply(apps, schema_editor):
    """Rename PowerConsumption specification key to PowerSupply"""
    DeviceModel = apps.get_model('devices', 'DeviceModel')
    
    for device_model in DeviceModel.objects.all():
        if device_model.specifications and 'PowerConsumption' in device_model.specifications:
            # Create a new specifications dict with the renamed key
            updated_specs = device_model.specifications.copy()
            
            # Move the value from PowerConsumption to PowerSupply
            updated_specs['PowerSupply'] = updated_specs.pop('PowerConsumption')
            
            # Save the updated specifications
            device_model.specifications = updated_specs
            device_model.save()
            
            print(f"Device Model {device_model.id}: Renamed 'PowerConsumption' -> 'PowerSupply' in {device_model.manufacturer} {device_model.model_name}")


def reverse_rename_power_supply_to_power_consumption(apps, schema_editor):
    """Reverse migration - rename PowerSupply back to PowerConsumption"""
    DeviceModel = apps.get_model('devices', 'DeviceModel')
    
    for device_model in DeviceModel.objects.all():
        if device_model.specifications and 'PowerSupply' in device_model.specifications:
            # Create a new specifications dict with the renamed key
            updated_specs = device_model.specifications.copy()
            
            # Move the value from PowerSupply to PowerConsumption
            updated_specs['PowerConsumption'] = updated_specs.pop('PowerSupply')
            
            # Save the updated specifications
            device_model.specifications = updated_specs
            device_model.save()


class Migration(migrations.Migration):
    dependencies = [
        ('devices', '0008_normalize_specification_keys'),
    ]

    operations = [
        migrations.RunPython(rename_power_consumption_to_power_supply, reverse_rename_power_supply_to_power_consumption),
    ]