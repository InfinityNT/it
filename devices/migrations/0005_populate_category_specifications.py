"""
Data migration to populate DeviceCategory.specifications from hardcoded templates.

This migrates the specification definitions from devices/spec_templates.py into
the DeviceCategory.specifications field, establishing the database as the single
source of truth for category specification schemas.
"""

from django.db import migrations


# Hardcoded templates from spec_templates.py - copied here to ensure migration
# works even if spec_templates.py is later removed
CATEGORY_SPEC_TEMPLATES = {
    'Laptop': [
        {"name": "CPUModel", "type": "text", "label": "CPU Model"},
        {"name": "RAM", "type": "text", "label": "RAM"},
        {"name": "Storage", "type": "text", "label": "Storage"},
        {"name": "GPU", "type": "text", "label": "Graphics Card"},
        {"name": "Display", "type": "text", "label": "Display"},
        {"name": "BatteryHealth", "type": "text", "label": "Battery Health"},
        {"name": "OperatingSystem", "type": "text", "label": "Operating System"},
        {"name": "WiFi", "type": "text", "label": "WiFi"},
        {"name": "Bluetooth", "type": "text", "label": "Bluetooth"},
        {"name": "Weight", "type": "text", "label": "Weight"},
        {"name": "Ports", "type": "text", "label": "Ports"},
    ],
    'Desktop': [
        {"name": "CPUModel", "type": "text", "label": "CPU Model"},
        {"name": "RAM", "type": "text", "label": "RAM"},
        {"name": "Storage", "type": "text", "label": "Storage"},
        {"name": "GPU", "type": "text", "label": "Graphics Card"},
        {"name": "OperatingSystem", "type": "text", "label": "Operating System"},
        {"name": "PowerSupply", "type": "text", "label": "Power Supply"},
        {"name": "ChassisType", "type": "text", "label": "Chassis Type"},
        {"name": "Ports", "type": "text", "label": "Ports"},
        {"name": "Ethernet", "type": "text", "label": "Ethernet"},
    ],
    'Monitor': [
        {"name": "ScreenSize", "type": "text", "label": "Screen Size"},
        {"name": "Display", "type": "text", "label": "Display/Resolution"},
        {"name": "Ports", "type": "text", "label": "Ports"},
        {"name": "PowerSupply", "type": "text", "label": "Power Supply"},
    ],
    'Printer': [
        {"name": "Capacity", "type": "text", "label": "Capacity"},
        {"name": "Network", "type": "text", "label": "Network"},
        {"name": "Dimensions", "type": "text", "label": "Dimensions"},
        {"name": "PowerSupply", "type": "text", "label": "Power Supply"},
    ],
    'Phone': [
        {"name": "ScreenSize", "type": "text", "label": "Screen Size"},
        {"name": "Storage", "type": "text", "label": "Storage"},
        {"name": "RAM", "type": "text", "label": "RAM"},
        {"name": "OperatingSystem", "type": "text", "label": "Operating System"},
        {"name": "BatteryHealth", "type": "text", "label": "Battery Health"},
        {"name": "Network", "type": "text", "label": "Network"},
    ],
    'Tablet': [
        {"name": "ScreenSize", "type": "text", "label": "Screen Size"},
        {"name": "Storage", "type": "text", "label": "Storage"},
        {"name": "RAM", "type": "text", "label": "RAM"},
        {"name": "OperatingSystem", "type": "text", "label": "Operating System"},
        {"name": "BatteryHealth", "type": "text", "label": "Battery Health"},
        {"name": "WiFi", "type": "text", "label": "WiFi"},
        {"name": "Weight", "type": "text", "label": "Weight"},
    ],
    'Server': [
        {"name": "CPUModel", "type": "text", "label": "CPU Model"},
        {"name": "RAM", "type": "text", "label": "RAM"},
        {"name": "Storage", "type": "text", "label": "Storage"},
        {"name": "RAID", "type": "text", "label": "RAID Configuration"},
        {"name": "Network", "type": "text", "label": "Network"},
        {"name": "PowerSupply", "type": "text", "label": "Power Supply"},
        {"name": "ChassisType", "type": "text", "label": "Chassis Type"},
    ],
    'Network Equipment': [
        {"name": "Ports", "type": "text", "label": "Ports"},
        {"name": "Network", "type": "text", "label": "Network"},
        {"name": "PowerSupply", "type": "text", "label": "Power Supply"},
        {"name": "Firmware", "type": "text", "label": "Firmware Version"},
    ],
}


def populate_category_specifications(apps, schema_editor):
    """
    Populate DeviceCategory.specifications from templates.

    The template format is already in the correct database format:
        [{"name": "CPUModel", "type": "text", "label": "CPU Model"}, ...]
    """
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')

    for category in DeviceCategory.objects.all():
        # Skip if category already has specifications defined
        if category.specifications:
            continue

        # Get template for this category name (already in list format with labels)
        specifications = CATEGORY_SPEC_TEMPLATES.get(category.name, [])

        if specifications:
            category.specifications = specifications
            category.save()


def reverse_populate_category_specifications(apps, schema_editor):
    """
    Reverse migration - clear specifications field.
    """
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')
    DeviceCategory.objects.update(specifications=[])


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0004_add_is_general_and_specifications_to_category'),
    ]

    operations = [
        migrations.RunPython(
            populate_category_specifications,
            reverse_populate_category_specifications,
        ),
    ]
