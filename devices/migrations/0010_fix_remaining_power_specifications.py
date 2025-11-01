from django.db import migrations


def fix_remaining_power_specifications(apps, schema_editor):
    """Fix any remaining power-related specification keys that weren't caught"""
    DeviceModel = apps.get_model('devices', 'DeviceModel')
    
    # Additional power-related key variations to catch
    power_variations = [
        'PSU', 'Psu', 'psu',
        'Power_Supply', 'power_supply', 'POWER_SUPPLY',
        'PowerSupply', 'powersupply', 'POWERSUPPLY',
        'Power_Source', 'power_source', 'POWER_SOURCE',
        'Power Unit', 'power unit', 'POWER UNIT',
        'PSU_Type', 'psu_type', 'PSU Type',
        'Power_Rating', 'power_rating', 'POWER_RATING',
        'Supply', 'supply', 'SUPPLY',
        'Wattage', 'wattage', 'WATTAGE',
        'redundant_psu', 'redundant psu', 'REDUNDANT_PSU',
        'redundant_power', 'redundant power', 'REDUNDANT_POWER'
    ]
    
    for device_model in DeviceModel.objects.all():
        if device_model.specifications:
            updated_specs = device_model.specifications.copy()
            changed = False
            
            for old_key, value in device_model.specifications.items():
                # Check if this key is a power-related variation
                if old_key in power_variations:
                    # Remove the old key and add it as PowerSupply
                    updated_specs.pop(old_key)
                    updated_specs['PowerSupply'] = value
                    changed = True
                    print(f"Device Model {device_model.id}: Fixed power spec '{old_key}' -> 'PowerSupply' = '{value}'")
                elif any(power_word in old_key.lower() for power_word in ['power', 'psu', 'supply', 'watt']):
                    # Catch any other power-related keys we might have missed
                    if old_key != 'PowerSupply':  # Don't change already correct keys
                        updated_specs.pop(old_key)
                        updated_specs['PowerSupply'] = value
                        changed = True
                        print(f"Device Model {device_model.id}: Fixed power spec '{old_key}' -> 'PowerSupply' = '{value}'")
            
            # Save the updated specifications if any changes were made
            if changed:
                device_model.specifications = updated_specs
                device_model.save()
                print(f"Updated Device Model {device_model.id}: {device_model.manufacturer} {device_model.model_name}")


def reverse_fix_power_specifications(apps, schema_editor):
    """Reverse migration - not implemented as it would lose information about original keys"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('devices', '0009_rename_power_consumption_to_power_supply'),
    ]

    operations = [
        migrations.RunPython(fix_remaining_power_specifications, reverse_fix_power_specifications),
    ]