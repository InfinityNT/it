import random
import string
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import Device, DeviceCategory, DeviceModel, DeviceHistory
from employees.models import Employee
from core.models import User


class Command(BaseCommand):
    help = 'Generate comprehensive sample device data with enhanced fields'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=50, help='Number of devices to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing device data first')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing device data...')
            Device.objects.all().delete()
            DeviceHistory.objects.all().delete()
            DeviceCategory.objects.all().delete()
            DeviceModel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Device data cleared.'))

        count = options['count']
        self.stdout.write(f'Creating {count} sample devices...')

        # Create categories
        categories = self.create_categories()
        
        # Create device models
        models = self.create_device_models(categories)
        
        # Get employees for assignment
        employees = list(Employee.objects.all())
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Create devices
        devices_created = 0
        for i in range(count):
            device = self.create_device(models, employees, admin_user)
            if device:
                devices_created += 1
                if devices_created % 10 == 0:
                    self.stdout.write(f'Created {devices_created} devices...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {devices_created} sample devices!')
        )

    def create_categories(self):
        """Create device categories"""
        categories_data = [
            ('Laptop', 'Portable computers for employee use'),
            ('Desktop', 'Desktop computers and workstations'),
            ('Phone', 'Mobile phones and smartphones'),
            ('Tablet', 'Tablets and iPad devices'),
            ('Monitor', 'Computer monitors and displays'),
            ('Printer', 'Printers and printing equipment'),
            ('Server', 'Server equipment and infrastructure'),
            ('Networking', 'Network switches, routers, and equipment'),
            ('Audio/Video', 'Audio and video equipment'),
            ('Accessories', 'Computer accessories and peripherals'),
        ]
        
        categories = []
        for name, description in categories_data:
            category, created = DeviceCategory.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            categories.append(category)
        
        return categories

    def create_device_models(self, categories):
        """Create device models with specifications"""
        models_data = [
            # Laptops
            ('Laptop', 'Apple', 'MacBook Pro 14" M3', {
                'CPU': 'Apple M3 Pro',
                'RAM': '18GB',
                'Storage': '512GB SSD',
                'Display': '14.2" Liquid Retina XDR',
                'Graphics': 'Apple M3 Pro GPU',
                'Battery': '70Wh',
                'Ports': 'Thunderbolt 4, HDMI, SD Card'
            }),
            ('Laptop', 'Dell', 'Latitude 7430', {
                'CPU': 'Intel Core i7-1265U',
                'RAM': '16GB DDR4',
                'Storage': '512GB NVMe SSD',
                'Display': '14" FHD',
                'Graphics': 'Intel Iris Xe',
                'Battery': '58Wh',
                'Ports': 'USB-A, USB-C, HDMI, Ethernet'
            }),
            ('Laptop', 'HP', 'EliteBook 840 G9', {
                'CPU': 'Intel Core i5-1235U',
                'RAM': '16GB DDR4',
                'Storage': '256GB NVMe SSD',
                'Display': '14" FHD',
                'Graphics': 'Intel Iris Xe',
                'Battery': '51Wh',
                'Ports': 'USB-A, USB-C, HDMI'
            }),
            ('Laptop', 'Lenovo', 'ThinkPad X1 Carbon Gen 11', {
                'CPU': 'Intel Core i7-1355U',
                'RAM': '32GB LPDDR5',
                'Storage': '1TB NVMe SSD',
                'Display': '14" WUXGA',
                'Graphics': 'Intel Iris Xe',
                'Battery': '57Wh',
                'Ports': 'USB-A, USB-C, HDMI'
            }),
            
            # Desktops
            ('Desktop', 'Dell', 'OptiPlex 7010', {
                'CPU': 'Intel Core i7-13700',
                'RAM': '32GB DDR4',
                'Storage': '1TB NVMe SSD',
                'Graphics': 'Intel UHD Graphics 770',
                'Form Factor': 'Small Form Factor',
                'Ports': 'USB-A, USB-C, HDMI, DisplayPort'
            }),
            ('Desktop', 'HP', 'ProDesk 600 G9', {
                'CPU': 'Intel Core i5-12500',
                'RAM': '16GB DDR4',
                'Storage': '512GB NVMe SSD',
                'Graphics': 'Intel UHD Graphics 770',
                'Form Factor': 'Mini Tower',
                'Ports': 'USB-A, USB-C, HDMI, VGA'
            }),
            
            # Phones
            ('Phone', 'Apple', 'iPhone 15 Pro', {
                'Display': '6.1" Super Retina XDR',
                'Storage': '256GB',
                'Camera': '48MP Main, 12MP Ultra Wide',
                'Battery': '3274mAh',
                'Connectivity': '5G, WiFi 6E, Bluetooth 5.3'
            }),
            ('Phone', 'Samsung', 'Galaxy S24', {
                'Display': '6.2" Dynamic AMOLED 2X',
                'Storage': '256GB',
                'Camera': '50MP Main, 12MP Ultra Wide',
                'Battery': '4000mAh',
                'Connectivity': '5G, WiFi 6E, Bluetooth 5.3'
            }),
            
            # Tablets
            ('Tablet', 'Apple', 'iPad Pro 12.9" M2', {
                'Display': '12.9" Liquid Retina XDR',
                'Storage': '256GB',
                'CPU': 'Apple M2',
                'Camera': '12MP Wide, 10MP Ultra Wide',
                'Battery': '10758mAh',
                'Connectivity': 'WiFi 6E, Bluetooth 5.3'
            }),
            ('Tablet', 'Microsoft', 'Surface Pro 9', {
                'Display': '13" PixelSense',
                'Storage': '256GB SSD',
                'CPU': 'Intel Core i5-1235U',
                'RAM': '8GB',
                'Camera': '5MP Front, 10MP Rear',
                'Battery': '47.36Wh'
            }),
            
            # Monitors
            ('Monitor', 'Dell', 'UltraSharp U2723QE', {
                'Size': '27"',
                'Resolution': '4K UHD (3840x2160)',
                'Panel Type': 'IPS',
                'Refresh Rate': '60Hz',
                'Ports': 'USB-C, HDMI, DisplayPort',
                'Stand': 'Height adjustable'
            }),
            ('Monitor', 'LG', '27UK850-W', {
                'Size': '27"',
                'Resolution': '4K UHD (3840x2160)',
                'Panel Type': 'IPS',
                'Refresh Rate': '60Hz',
                'Ports': 'USB-C, HDMI, DisplayPort',
                'HDR': 'HDR10'
            }),
            
            # Printers
            ('Printer', 'HP', 'LaserJet Pro 4025n', {
                'Type': 'Laser',
                'Color': 'Color',
                'Speed': '25 ppm',
                'Resolution': '600x600 dpi',
                'Connectivity': 'Ethernet, USB',
                'Duplex': 'Automatic'
            }),
            ('Printer', 'Canon', 'imageCLASS MF445dw', {
                'Type': 'Laser',
                'Color': 'Monochrome',
                'Speed': '38 ppm',
                'Resolution': '600x600 dpi',
                'Connectivity': 'WiFi, Ethernet, USB',
                'Duplex': 'Automatic'
            }),
            
            # Servers
            ('Server', 'Dell', 'PowerEdge R750', {
                'CPU': '2x Intel Xeon Silver 4314',
                'RAM': '64GB DDR4',
                'Storage': '4x 2TB NVMe SSD',
                'Form Factor': '2U Rack',
                'Network': '4x 1GbE, 2x 10GbE',
                'Power': 'Redundant 800W PSU'
            }),
            
            # Networking
            ('Networking', 'Cisco', 'Catalyst 9300-24T', {
                'Type': 'Managed Switch',
                'Ports': '24x 1GbE, 4x 10GbE SFP+',
                'Layer': 'Layer 3',
                'PoE': 'PoE+',
                'Stacking': 'Yes',
                'Management': 'Web, CLI, SNMP'
            }),
        ]
        
        models = []
        for category_name, manufacturer, model_name, specifications in models_data:
            category = next(c for c in categories if c.name == category_name)
            model, created = DeviceModel.objects.get_or_create(
                category=category,
                manufacturer=manufacturer,
                model_name=model_name,
                defaults={'specifications': specifications}
            )
            models.append(model)
        
        return models

    def create_device(self, models, employees, admin_user):
        """Create a single device with realistic data"""
        device_model = random.choice(models)
        
        # Generate unique asset tag
        attempts = 0
        while attempts < 10:
            asset_tag = f"{device_model.category.name[:3].upper()}-{random.randint(1000, 9999)}"
            if not Device.objects.filter(asset_tag=asset_tag).exists():
                break
            attempts += 1
        
        # Generate unique serial number
        attempts = 0
        while attempts < 10:
            serial_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if not Device.objects.filter(serial_number=serial_number).exists():
                break
            attempts += 1
        
        # Generate MAC address for network devices
        mac_address = None
        if device_model.category.name in ['Laptop', 'Desktop', 'Server', 'Networking']:
            # Generate unique MAC address
            attempts = 0
            while attempts < 10:
                mac_attempt = ':'.join([f'{random.randint(0, 255):02X}' for _ in range(6)])
                if not Device.objects.filter(mac_address=mac_attempt).exists():
                    mac_address = mac_attempt
                    break
                attempts += 1
        
        # Generate IP address for some devices
        ip_address = None
        if device_model.category.name in ['Laptop', 'Desktop', 'Server', 'Networking', 'Printer']:
            if random.random() < 0.7:  # 70% chance of having IP
                # Generate unique IP address
                attempts = 0
                while attempts < 10:
                    ip_attempt = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
                    if not Device.objects.filter(ip_address=ip_attempt).exists():
                        ip_address = ip_attempt
                        break
                    attempts += 1
        
        # Generate hostname for computers
        hostname = ''
        if device_model.category.name in ['Laptop', 'Desktop', 'Server']:
            hostname = f"{device_model.category.name.lower()}-{random.randint(100, 999)}"
        
        # Determine usage type
        usage_type = 'individual'
        shared_usage = None
        if device_model.category.name in ['Printer', 'Server', 'Networking']:
            usage_type = 'shared'
            shared_usage = random.choice(['shared', 'training', 'kiosk'])
        elif random.random() < 0.1:  # 10% chance for individual devices to be shared
            usage_type = 'shared'
            shared_usage = random.choice(['shared', 'training', 'kiosk'])
        
        # Generate location data
        location = random.choice([
            'Conference Room', 'Open Office', 'Executive Office', 'IT Room',
            'Reception', 'Training Room', 'Break Room', 'Storage'
        ])

        # Determine status and assignment
        status = random.choices(
            ['available', 'assigned', 'maintenance', 'retired'],
            weights=[30, 60, 5, 5]
        )[0]
        
        assigned_to = None
        assigned_date = None
        if status == 'assigned' and employees and usage_type == 'individual':
            assigned_to = random.choice(employees)
            assigned_date = timezone.now() - timedelta(days=random.randint(1, 365))
        
        # Generate notes
        notes_options = [
            '',
            'Requires special software configuration',
            'Backup device for critical operations',
            'Scheduled for replacement next quarter',
            'High-performance configuration for development',
            'Standard office configuration',
            'Refurbished device with extended warranty',
        ]
        notes = random.choice(notes_options)
        
        try:
            device = Device.objects.create(
                asset_tag=asset_tag,
                serial_number=serial_number,
                device_model=device_model,
                status=status,
                usage_type=usage_type,
                shared_usage=shared_usage,
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                location=location,
                assigned_to=assigned_to,
                assigned_date=assigned_date,
                notes=notes,
                created_by=admin_user
            )
            
            # Create initial history entry
            DeviceHistory.objects.create(
                device=device,
                action='created',
                new_status=status,
                notes=f'Device created with sample data',
                created_by=admin_user
            )
            
            # Create assignment history if assigned
            if assigned_to:
                DeviceHistory.objects.create(
                    device=device,
                    action='assigned',
                    new_status='assigned',
                    previous_status='available',
                    new_employee=assigned_to,
                    notes=f'Assigned to {assigned_to.get_full_name()}',
                    created_by=admin_user
                )
            
            return device
            
        except Exception as e:
            self.stderr.write(f'Error creating device {asset_tag}: {str(e)}')
            return None

    def generate_random_string(self, length=8):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))