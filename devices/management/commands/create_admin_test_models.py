from django.core.management.base import BaseCommand
from devices.models import DeviceManufacturer, DeviceVendor, DeviceCategory, DeviceModel


class Command(BaseCommand):
    help = 'Create additional test device models for admin testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating additional test device models...')
        
        # Get required objects
        try:
            laptop_cat = DeviceCategory.objects.get(name='Laptop')
            desktop_cat = DeviceCategory.objects.get(name='Desktop')
            monitor_cat = DeviceCategory.objects.get(name='Monitor')
            
            apple = DeviceManufacturer.objects.get(name='Apple')
            dell = DeviceManufacturer.objects.get(name='Dell')
            hp = DeviceManufacturer.objects.get(name='HP')
            
        except (DeviceCategory.DoesNotExist, DeviceManufacturer.DoesNotExist):
            self.stdout.write(self.style.ERROR('Required categories and manufacturers not found.'))
            return
        
        # Additional test models
        test_models = [
            {
                'category': laptop_cat,
                'manufacturer': 'Apple',
                'model_name': 'MacBook Pro 13" M2',
                'specs': {
                    'CPU': 'Apple M2',
                    'RAM': '16 GB',
                    'Storage': '512 GB SSD',
                    'Display': '13.3" Retina'
                }
            },
            {
                'category': desktop_cat,
                'manufacturer': 'Dell',
                'model_name': 'OptiPlex 7000',
                'specs': {
                    'CPU': 'Intel i7-12700',
                    'RAM': '16 GB',
                    'Storage': '512 GB SSD',
                    'GPU': 'Intel UHD Graphics 770'
                }
            },
            {
                'category': monitor_cat,
                'manufacturer': 'HP',
                'model_name': 'E24 G5',
                'specs': {
                    'Display': '24" FHD IPS',
                    'Resolution': '1920x1080',
                    'Refresh Rate': '60Hz',
                    'Ports': 'HDMI, DisplayPort, VGA'
                }
            },
        ]
        
        created_models = 0
        for model_data in test_models:
            device_model, created = DeviceModel.objects.get_or_create(
                category=model_data['category'],
                manufacturer=model_data['manufacturer'],
                model_name=model_data['model_name'],
                defaults={
                    'specifications': model_data.get('specs', {}),
                    'is_active': True
                }
            )
            if created:
                created_models += 1
                self.stdout.write(f'Created: {device_model}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_models} additional test device models'
            )
        )