"""Default specification templates for device categories"""

CATEGORY_SPEC_TEMPLATES = {
    'Laptop': {
        'CPUModel': '',
        'RAM': '',
        'Storage': '',
        'GPU': '',
        'Display': '',
        'BatteryHealth': '',
        'OperatingSystem': '',
        'WiFi': '',
        'Bluetooth': '',
        'Weight': '',
        'Ports': ''
    },
    'Desktop': {
        'CPUModel': '',
        'RAM': '',
        'Storage': '',
        'GPU': '',
        'OperatingSystem': '',
        'PowerSupply': '',
        'ChassisType': '',
        'Ports': '',
        'Ethernet': ''
    },
    'Monitor': {
        'ScreenSize': '',
        'Display': '',
        'Ports': '',
        'PowerSupply': ''
    },
    'Printer': {
        'Capacity': '',
        'Network': '',
        'Dimensions': '',
        'PowerSupply': ''
    },
    'Phone': {
        'ScreenSize': '',
        'Storage': '',
        'RAM': '',
        'OperatingSystem': '',
        'BatteryHealth': '',
        'Network': ''
    },
    'Tablet': {
        'ScreenSize': '',
        'Storage': '',
        'RAM': '',
        'OperatingSystem': '',
        'BatteryHealth': '',
        'WiFi': '',
        'Weight': ''
    },
    'Server': {
        'CPUModel': '',
        'RAM': '',
        'Storage': '',
        'RAID': '',
        'Network': '',
        'PowerSupply': '',
        'ChassisType': ''
    },
    'Network Equipment': {
        'Ports': '',
        'Network': '',
        'PowerSupply': '',
        'Firmware': ''
    }
}

# Display name mapping for spec keys
SPEC_DISPLAY_NAMES = {
    'CPUModel': 'CPU Model',
    'RAM': 'RAM',
    'Storage': 'Storage',
    'GPU': 'Graphics Card',
    'Display': 'Display/Resolution',
    'BatteryHealth': 'Battery Health',
    'OperatingSystem': 'Operating System',
    'WiFi': 'WiFi',
    'Bluetooth': 'Bluetooth',
    'Weight': 'Weight',
    'Ports': 'Ports',
    'PowerSupply': 'Power Supply',
    'ChassisType': 'Chassis Type',
    'Ethernet': 'Ethernet',
    'ScreenSize': 'Screen Size',
    'Capacity': 'Capacity',
    'Network': 'Network',
    'Dimensions': 'Dimensions',
    'RAID': 'RAID Configuration',
    'Firmware': 'Firmware Version'
}


def get_spec_template(category_name):
    """Get default spec template for a category"""
    return CATEGORY_SPEC_TEMPLATES.get(category_name, {
        'CPUModel': '',
        'RAM': '',
        'Storage': ''
    })


def get_spec_display_name(key):
    """Get display name for a spec key"""
    return SPEC_DISPLAY_NAMES.get(key, key)
