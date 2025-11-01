from django.core.management.base import BaseCommand
from devices.models import DeviceManufacturer, DeviceVendor, DeviceCategory


class Command(BaseCommand):
    help = 'Create predefined manufacturers, vendors, and categories'

    def handle(self, *args, **options):
        self.stdout.write('Creating predefined manufacturers, vendors, and categories...')
        
        # Create manufacturers
        manufacturers = [
            {'name': 'Apple', 'website': 'https://www.apple.com'},
            {'name': 'Dell', 'website': 'https://www.dell.com'},
            {'name': 'HP', 'website': 'https://www.hp.com'},
            {'name': 'Lenovo', 'website': 'https://www.lenovo.com'},
            {'name': 'Microsoft', 'website': 'https://www.microsoft.com'},
            {'name': 'ASUS', 'website': 'https://www.asus.com'},
            {'name': 'Acer', 'website': 'https://www.acer.com'},
            {'name': 'Samsung', 'website': 'https://www.samsung.com'},
            {'name': 'Canon', 'website': 'https://www.canon.com'},
            {'name': 'Epson', 'website': 'https://www.epson.com'},
            {'name': 'Cisco', 'website': 'https://www.cisco.com'},
            {'name': 'Ubiquiti', 'website': 'https://www.ubiquiti.com'},
            {'name': 'Netgear', 'website': 'https://www.netgear.com'},
            {'name': 'TP-Link', 'website': 'https://www.tp-link.com'},
            {'name': 'Logitech', 'website': 'https://www.logitech.com'},
            {'name': 'Brother', 'website': 'https://www.brother.com'},
            {'name': 'Sony', 'website': 'https://www.sony.com'},
            {'name': 'LG', 'website': 'https://www.lg.com'},
            {'name': 'Intel', 'website': 'https://www.intel.com'},
            {'name': 'AMD', 'website': 'https://www.amd.com'},
        ]
        
        created_manufacturers = 0
        for manufacturer_data in manufacturers:
            manufacturer, created = DeviceManufacturer.objects.get_or_create(
                name=manufacturer_data['name'],
                defaults={
                    'website': manufacturer_data['website'],
                    'is_active': True
                }
            )
            if created:
                created_manufacturers += 1
        
        self.stdout.write(f'Created {created_manufacturers} manufacturers')
        
        # Create vendors
        vendors = [
            {'name': 'Amazon', 'website': 'https://www.amazon.com'},
            {'name': 'Best Buy', 'website': 'https://www.bestbuy.com'},
            {'name': 'CDW', 'website': 'https://www.cdw.com'},
            {'name': 'Newegg', 'website': 'https://www.newegg.com'},
            {'name': 'B&H Photo', 'website': 'https://www.bhphotovideo.com'},
            {'name': 'Staples', 'website': 'https://www.staples.com'},
            {'name': 'Office Depot', 'website': 'https://www.officedepot.com'},
            {'name': 'Costco', 'website': 'https://www.costco.com'},
            {'name': 'Sam\'s Club', 'website': 'https://www.samsclub.com'},
            {'name': 'Walmart', 'website': 'https://www.walmart.com'},
            {'name': 'CompUSA', 'website': ''},
            {'name': 'TigerDirect', 'website': 'https://www.tigerdirect.com'},
            {'name': 'Insight', 'website': 'https://www.insight.com'},
            {'name': 'Connection', 'website': 'https://www.connection.com'},
            {'name': 'Micro Center', 'website': 'https://www.microcenter.com'},
        ]
        
        created_vendors = 0
        for vendor_data in vendors:
            vendor, created = DeviceVendor.objects.get_or_create(
                name=vendor_data['name'],
                defaults={
                    'website': vendor_data['website'],
                    'is_active': True
                }
            )
            if created:
                created_vendors += 1
        
        self.stdout.write(f'Created {created_vendors} vendors')
        
        # Create categories
        categories = [
            {'name': 'Laptop', 'description': 'Portable computers'},
            {'name': 'Desktop', 'description': 'Desktop computers'},
            {'name': 'Monitor', 'description': 'Computer monitors and displays'},
            {'name': 'Phone', 'description': 'Mobile phones and smartphones'},
            {'name': 'Tablet', 'description': 'Tablets and iPads'},
            {'name': 'Printer', 'description': 'Printers and print devices'},
            {'name': 'Scanner', 'description': 'Document scanners'},
            {'name': 'Server', 'description': 'Server hardware'},
            {'name': 'Network Equipment', 'description': 'Routers, switches, access points'},
            {'name': 'Storage', 'description': 'NAS, external drives, storage devices'},
            {'name': 'Projector', 'description': 'Projectors and presentation devices'},
            {'name': 'Webcam', 'description': 'Web cameras and video devices'},
            {'name': 'Headset', 'description': 'Headphones and headsets'},
            {'name': 'Keyboard', 'description': 'Keyboards and input devices'},
            {'name': 'Mouse', 'description': 'Mice and pointing devices'},
            {'name': 'Dock', 'description': 'Docking stations and hubs'},
            {'name': 'Cable', 'description': 'Cables and adapters'},
            {'name': 'UPS', 'description': 'Uninterruptible power supplies'},
            {'name': 'Other', 'description': 'Other IT equipment'},
        ]
        
        created_categories = 0
        for category_data in categories:
            category, created = DeviceCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_categories += 1
        
        self.stdout.write(f'Created {created_categories} categories')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_manufacturers} manufacturers, '
                f'{created_vendors} vendors, and {created_categories} categories'
            )
        )