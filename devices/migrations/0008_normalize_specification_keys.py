from django.db import migrations


def normalize_specification_keys(apps, schema_editor):
    """Normalize specification keys to use standardized names"""
    DeviceModel = apps.get_model('devices', 'DeviceModel')
    
    # Mapping from legacy/inconsistent keys to standardized keys
    key_mapping = {
        # CPU variations
        'cpu': 'CPUModel',
        'CPU': 'CPUModel',
        'processor': 'CPUModel',
        
        # Power variations
        'power': 'PowerSupply',
        'power_consumption': 'PowerSupply',
        'power_supply': 'PowerSupply',
        'psu': 'PowerSupply',
        'watts': 'PowerSupply',
        
        # Memory variations
        'ram': 'RAM',
        'memory': 'RAM',
        'Memory': 'RAM',
        
        # Storage variations
        'storage': 'Storage',
        'Storage': 'Storage',
        'hdd': 'Storage',
        'ssd': 'Storage',
        'disk': 'Storage',
        
        # Graphics variations
        'gpu': 'GPU',
        'graphics': 'GPU',
        'video_card': 'GPU',
        
        # Display variations
        'display': 'Display',
        'screen': 'Display',
        'monitor': 'Display',
        
        # OS variations
        'os': 'OperatingSystem',
        'operating_system': 'OperatingSystem',
        'OS': 'OperatingSystem',
        
        # Network variations
        'wifi': 'WiFi',
        'wireless': 'WiFi',
        'bluetooth': 'Bluetooth',
        'ethernet': 'Ethernet',
        'network': 'Network',
        
        # Physical variations
        'weight': 'Weight',
        'dimensions': 'Dimensions',
        'size': 'Dimensions',
        'color': 'Color',
        'colour': 'Color',
        
        # Other variations
        'serial': 'SerialNumber',
        'serial_number': 'SerialNumber',
        'model': 'ModelNumber',
        'model_number': 'ModelNumber',
        'part': 'PartNumber',
        'part_number': 'PartNumber',
        'bios': 'BIOSVersion',
        'firmware': 'Firmware',
        'battery': 'BatteryHealth',
        'ports': 'Ports',
        'capacity': 'Capacity',
        'manufacturer': 'Manufacturer',
        'brand': 'Manufacturer',
    }
    
    for device_model in DeviceModel.objects.all():
        if device_model.specifications:
            updated_specs = {}
            changed = False
            
            for old_key, value in device_model.specifications.items():
                # Check if this key needs to be normalized
                if old_key in key_mapping:
                    new_key = key_mapping[old_key]
                    updated_specs[new_key] = value
                    changed = True
                    print(f"Device Model {device_model.id}: Normalized '{old_key}' -> '{new_key}'")
                else:
                    # Keep the original key if no mapping found
                    updated_specs[old_key] = value
            
            # Save the updated specifications if any changes were made
            if changed:
                device_model.specifications = updated_specs
                device_model.save()
                print(f"Updated Device Model {device_model.id}: {device_model.manufacturer} {device_model.model_name}")


def reverse_normalize_specification_keys(apps, schema_editor):
    """Reverse migration - not implemented as it would lose information"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('devices', '0007_populate_it_asset_tag'),
    ]

    operations = [
        migrations.RunPython(normalize_specification_keys, reverse_normalize_specification_keys),
    ]