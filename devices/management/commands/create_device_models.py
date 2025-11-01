from django.core.management.base import BaseCommand
from devices.models import DeviceManufacturer, DeviceVendor, DeviceCategory, DeviceModel


class Command(BaseCommand):
    help = 'Create predefined device models'

    def handle(self, *args, **options):
        self.stdout.write('Creating predefined device models...')
        
        # Get categories and manufacturers
        try:
            laptop_cat = DeviceCategory.objects.get(name='Laptop')
            desktop_cat = DeviceCategory.objects.get(name='Desktop')
            monitor_cat = DeviceCategory.objects.get(name='Monitor')
            phone_cat = DeviceCategory.objects.get(name='Phone')
            tablet_cat = DeviceCategory.objects.get(name='Tablet')
            printer_cat = DeviceCategory.objects.get(name='Printer')
        except DeviceCategory.DoesNotExist:
            self.stdout.write(self.style.ERROR('Categories not found. Run create_predefined_data first.'))
            return
        
        try:
            apple = DeviceManufacturer.objects.get(name='Apple')
            dell = DeviceManufacturer.objects.get(name='Dell')
            hp = DeviceManufacturer.objects.get(name='HP')
            lenovo = DeviceManufacturer.objects.get(name='Lenovo')
            microsoft = DeviceManufacturer.objects.get(name='Microsoft')
            samsung = DeviceManufacturer.objects.get(name='Samsung')
            canon = DeviceManufacturer.objects.get(name='Canon')
            epson = DeviceManufacturer.objects.get(name='Epson')
        except DeviceManufacturer.DoesNotExist:
            self.stdout.write(self.style.ERROR('Manufacturers not found. Run create_predefined_data first.'))
            return
        
        # Define device models
        device_models = [
            # Apple Laptops
            {'category': laptop_cat, 'manufacturer': 'Apple', 'model_name': 'MacBook Air M1', 'specs': {'CPU': 'Apple M1', 'RAM': '8 GB', 'Storage': '256 GB SSD', 'Display': '13.3" Retina'}},
            {'category': laptop_cat, 'manufacturer': 'Apple', 'model_name': 'MacBook Air M2', 'specs': {'CPU': 'Apple M2', 'RAM': '8 GB', 'Storage': '256 GB SSD', 'Display': '13.6" Liquid Retina'}},
            {'category': laptop_cat, 'manufacturer': 'Apple', 'model_name': 'MacBook Pro 13" M1', 'specs': {'CPU': 'Apple M1', 'RAM': '8 GB', 'Storage': '256 GB SSD', 'Display': '13.3" Retina'}},
            {'category': laptop_cat, 'manufacturer': 'Apple', 'model_name': 'MacBook Pro 14" M2', 'specs': {'CPU': 'Apple M2 Pro', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '14.2" Liquid Retina XDR'}},
            {'category': laptop_cat, 'manufacturer': 'Apple', 'model_name': 'MacBook Pro 16" M2', 'specs': {'CPU': 'Apple M2 Pro', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '16.2" Liquid Retina XDR'}},
            
            # Dell Laptops
            {'category': laptop_cat, 'manufacturer': 'Dell', 'model_name': 'Latitude 7420', 'specs': {'CPU': 'Intel i7-1185G7', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '14" FHD'}},
            {'category': laptop_cat, 'manufacturer': 'Dell', 'model_name': 'Latitude 9520', 'specs': {'CPU': 'Intel i7-1185G7', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '15" FHD'}},
            {'category': laptop_cat, 'manufacturer': 'Dell', 'model_name': 'XPS 13 9320', 'specs': {'CPU': 'Intel i7-1260P', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '13.4" FHD+'}},
            {'category': laptop_cat, 'manufacturer': 'Dell', 'model_name': 'Precision 3570', 'specs': {'CPU': 'Intel i7-1270P', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'Display': '15.6" FHD'}},
            
            # HP Laptops
            {'category': laptop_cat, 'manufacturer': 'HP', 'model_name': 'EliteBook 840 G9', 'specs': {'CPU': 'Intel i7-1265U', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '14" FHD'}},
            {'category': laptop_cat, 'manufacturer': 'HP', 'model_name': 'ProBook 450 G9', 'specs': {'CPU': 'Intel i5-1235U', 'RAM': '8 GB', 'Storage': '256 GB SSD', 'Display': '15.6" FHD'}},
            {'category': laptop_cat, 'manufacturer': 'HP', 'model_name': 'ZBook Studio G9', 'specs': {'CPU': 'Intel i7-12700H', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'Display': '15.6" 4K DreamColor'}},
            
            # Lenovo Laptops
            {'category': laptop_cat, 'manufacturer': 'Lenovo', 'model_name': 'ThinkPad X1 Carbon Gen 10', 'specs': {'CPU': 'Intel i7-1260P', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '14" WUXGA'}},
            {'category': laptop_cat, 'manufacturer': 'Lenovo', 'model_name': 'ThinkPad T14s Gen 3', 'specs': {'CPU': 'Intel i7-1265U', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '14" FHD'}},
            {'category': laptop_cat, 'manufacturer': 'Lenovo', 'model_name': 'ThinkPad P1 Gen 5', 'specs': {'CPU': 'Intel i7-12700H', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'Display': '16" 4K OLED'}},
            
            # Microsoft Laptops
            {'category': laptop_cat, 'manufacturer': 'Microsoft', 'model_name': 'Surface Laptop 5', 'specs': {'CPU': 'Intel i7-1255U', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'Display': '13.5" PixelSense'}},
            {'category': laptop_cat, 'manufacturer': 'Microsoft', 'model_name': 'Surface Book 3', 'specs': {'CPU': 'Intel i7-1065G7', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'Display': '15" PixelSense'}},
            
            # Apple Desktops
            {'category': desktop_cat, 'manufacturer': 'Apple', 'model_name': 'Mac Studio M1 Max', 'specs': {'CPU': 'Apple M1 Max', 'RAM': '32 GB', 'Storage': '512 GB SSD', 'GPU': 'M1 Max 24-core'}},
            {'category': desktop_cat, 'manufacturer': 'Apple', 'model_name': 'Mac Pro 2019', 'specs': {'CPU': 'Intel Xeon W-3245', 'RAM': '32 GB', 'Storage': '256 GB SSD', 'GPU': 'Radeon Pro 580X'}},
            {'category': desktop_cat, 'manufacturer': 'Apple', 'model_name': 'iMac 24" M1', 'specs': {'CPU': 'Apple M1', 'RAM': '8 GB', 'Storage': '256 GB SSD', 'Display': '24" 4.5K Retina'}},
            
            # Dell Desktops
            {'category': desktop_cat, 'manufacturer': 'Dell', 'model_name': 'OptiPlex 7090', 'specs': {'CPU': 'Intel i7-11700', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'GPU': 'Intel UHD Graphics 750'}},
            {'category': desktop_cat, 'manufacturer': 'Dell', 'model_name': 'Precision 3660', 'specs': {'CPU': 'Intel i7-12700', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'GPU': 'NVIDIA T1000'}},
            
            # HP Desktops
            {'category': desktop_cat, 'manufacturer': 'HP', 'model_name': 'EliteDesk 800 G9', 'specs': {'CPU': 'Intel i7-12700', 'RAM': '16 GB', 'Storage': '512 GB SSD', 'GPU': 'Intel UHD Graphics 770'}},
            {'category': desktop_cat, 'manufacturer': 'HP', 'model_name': 'Z4 G5 Workstation', 'specs': {'CPU': 'Intel Xeon W-2245', 'RAM': '32 GB', 'Storage': '1 TB SSD', 'GPU': 'NVIDIA RTX A4000'}},
            
            # Monitors
            {'category': monitor_cat, 'manufacturer': 'Dell', 'model_name': 'UltraSharp U2723QE', 'specs': {'Display': '27" 4K IPS', 'Resolution': '3840x2160', 'Refresh Rate': '60Hz', 'Ports': 'USB-C, HDMI, DisplayPort'}},
            {'category': monitor_cat, 'manufacturer': 'HP', 'model_name': 'EliteDisplay E27 G5', 'specs': {'Display': '27" QHD IPS', 'Resolution': '2560x1440', 'Refresh Rate': '75Hz', 'Ports': 'HDMI, DisplayPort, VGA'}},
            {'category': monitor_cat, 'manufacturer': 'Samsung', 'model_name': 'Odyssey G7 27"', 'specs': {'Display': '27" QLED Curved', 'Resolution': '2560x1440', 'Refresh Rate': '240Hz', 'Ports': 'HDMI, DisplayPort'}},
            
            # Phones
            {'category': phone_cat, 'manufacturer': 'Apple', 'model_name': 'iPhone 14', 'specs': {'Display': '6.1" Super Retina XDR', 'Storage': '128 GB', 'Camera': 'Dual 12MP', 'OS': 'iOS 16'}},
            {'category': phone_cat, 'manufacturer': 'Apple', 'model_name': 'iPhone 14 Pro', 'specs': {'Display': '6.1" Super Retina XDR ProMotion', 'Storage': '128 GB', 'Camera': 'Triple 48MP', 'OS': 'iOS 16'}},
            {'category': phone_cat, 'manufacturer': 'Samsung', 'model_name': 'Galaxy S23', 'specs': {'Display': '6.1" Dynamic AMOLED 2X', 'Storage': '128 GB', 'Camera': 'Triple 50MP', 'OS': 'Android 13'}},
            
            # Tablets
            {'category': tablet_cat, 'manufacturer': 'Apple', 'model_name': 'iPad Pro 12.9" M2', 'specs': {'Display': '12.9" Liquid Retina XDR', 'Storage': '128 GB', 'CPU': 'Apple M2', 'OS': 'iPadOS 16'}},
            {'category': tablet_cat, 'manufacturer': 'Apple', 'model_name': 'iPad Air 5th Gen', 'specs': {'Display': '10.9" Liquid Retina', 'Storage': '64 GB', 'CPU': 'Apple M1', 'OS': 'iPadOS 15'}},
            {'category': tablet_cat, 'manufacturer': 'Microsoft', 'model_name': 'Surface Pro 9', 'specs': {'Display': '13" PixelSense Flow', 'Storage': '128 GB', 'CPU': 'Intel i5-1235U', 'OS': 'Windows 11'}},
            
            # Printers
            {'category': printer_cat, 'manufacturer': 'Canon', 'model_name': 'imageCLASS MF445dw', 'specs': {'Type': 'Laser Multifunction', 'Print Speed': '40 ppm', 'Resolution': '600x600 dpi', 'Connectivity': 'Wi-Fi, Ethernet, USB'}},
            {'category': printer_cat, 'manufacturer': 'HP', 'model_name': 'LaserJet Pro M404n', 'specs': {'Type': 'Laser Printer', 'Print Speed': '38 ppm', 'Resolution': '4800x600 dpi', 'Connectivity': 'Ethernet, USB'}},
            {'category': printer_cat, 'manufacturer': 'Epson', 'model_name': 'EcoTank ET-4760', 'specs': {'Type': 'Inkjet Multifunction', 'Print Speed': '15 ppm', 'Resolution': '4800x1200 dpi', 'Connectivity': 'Wi-Fi, Ethernet, USB'}},
        ]
        
        created_models = 0
        for model_data in device_models:
            # Get manufacturer object
            try:
                manufacturer_obj = DeviceManufacturer.objects.get(name=model_data['manufacturer'])
            except DeviceManufacturer.DoesNotExist:
                self.stdout.write(f"Manufacturer {model_data['manufacturer']} not found, skipping model {model_data['model_name']}")
                continue
            
            device_model, created = DeviceModel.objects.get_or_create(
                category=model_data['category'],
                manufacturer=model_data['manufacturer'],  # Still using CharField for now
                model_name=model_data['model_name'],
                defaults={
                    'specifications': model_data.get('specs', {}),
                    'is_active': True
                }
            )
            if created:
                created_models += 1
        
        self.stdout.write(f'Created {created_models} device models')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_models} device models'
            )
        )