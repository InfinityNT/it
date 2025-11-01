from django.core.management.base import BaseCommand
from django.db import transaction
from devices.models import Device, DeviceHistory
from core.models import User


class Command(BaseCommand):
    help = 'Check and fix data integrity issues across the system'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Fix issues found (otherwise just report)')
        parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    def handle(self, *args, **options):
        fix_issues = options['fix']
        verbose = options['verbose']
        
        self.stdout.write('=== DATA INTEGRITY CHECK ===')
        self.stdout.write('')
        
        issues_found = 0
        issues_fixed = 0
        
        # Check 1: Devices with assigned status but no assigned employee
        problematic_devices = Device.objects.filter(assigned_to__isnull=True, status='assigned')
        if problematic_devices.exists():
            issues_found += problematic_devices.count()
            self.stdout.write(
                self.style.WARNING(f'Found {problematic_devices.count()} devices with "assigned" status but no assigned employee')
            )
            
            if verbose:
                for device in problematic_devices:
                    self.stdout.write(f'  - {device.asset_tag} ({device.device_model})')
            
            if fix_issues:
                admin_user = User.objects.filter(is_superuser=True).first()
                with transaction.atomic():
                    for device in problematic_devices:
                        old_status = device.status
                        device.status = 'available'
                        device.assigned_date = None
                        device.save()
                        
                        # Create history record
                        DeviceHistory.objects.create(
                            device=device,
                            action='status_change',
                            previous_status=old_status,
                            new_status='available',
                            notes='Auto-fix: removed assigned status without assigned employee',
                            created_by=admin_user
                        )
                        issues_fixed += 1
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Fixed {issues_fixed} devices'))
        
        # Check 2: Devices assigned to employees but status not assigned
        mismatched_status = Device.objects.filter(assigned_to__isnull=False).exclude(status='assigned')
        if mismatched_status.exists():
            issues_found += mismatched_status.count()
            self.stdout.write(
                self.style.WARNING(f'Found {mismatched_status.count()} devices assigned to employees but status is not "assigned"')
            )
            
            if verbose:
                for device in mismatched_status:
                    self.stdout.write(f'  - {device.asset_tag}: status={device.status}, assigned_to={device.assigned_to}')
            
            if fix_issues:
                admin_user = User.objects.filter(is_superuser=True).first()
                with transaction.atomic():
                    for device in mismatched_status:
                        old_status = device.status
                        device.status = 'assigned'
                        if not device.assigned_date:
                            device.assigned_date = device.updated_at
                        device.save()
                        
                        # Create history record
                        DeviceHistory.objects.create(
                            device=device,
                            action='status_change',
                            previous_status=old_status,
                            new_status='assigned',
                            notes='Auto-fix: updated status to match employee assignment',
                            created_by=admin_user
                        )
                        issues_fixed += 1
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Fixed {issues_fixed - (issues_fixed - mismatched_status.count())} devices'))
        
        # Check 3: Shared usage validation
        shared_usage_mismatch = Device.objects.filter(shared_usage__isnull=False).exclude(usage_type='shared')
        if shared_usage_mismatch.exists():
            issues_found += shared_usage_mismatch.count()
            self.stdout.write(
                self.style.WARNING(f'Found {shared_usage_mismatch.count()} devices with shared_usage but usage_type is not "shared"')
            )
            
            if fix_issues:
                admin_user = User.objects.filter(is_superuser=True).first()
                with transaction.atomic():
                    for device in shared_usage_mismatch:
                        device.usage_type = 'shared'
                        device.save()
                        
                        # Create history record
                        DeviceHistory.objects.create(
                            device=device,
                            action='updated',
                            notes='Auto-fix: set usage_type to shared to match shared_usage',
                            created_by=admin_user
                        )
                        issues_fixed += 1
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Fixed {shared_usage_mismatch.count()} devices'))
        
        # Check 4: Shared devices without shared_usage specified
        shared_without_usage = Device.objects.filter(usage_type='shared', shared_usage__isnull=True)
        if shared_without_usage.exists():
            issues_found += shared_without_usage.count()
            self.stdout.write(
                self.style.WARNING(f'Found {shared_without_usage.count()} devices with usage_type="shared" but no shared_usage specified')
            )
            
            if fix_issues:
                admin_user = User.objects.filter(is_superuser=True).first()
                with transaction.atomic():
                    for device in shared_without_usage:
                        device.shared_usage = 'shared'  # Default to 'shared'
                        device.save()
                        
                        # Create history record
                        DeviceHistory.objects.create(
                            device=device,
                            action='updated',
                            notes='Auto-fix: set default shared_usage for shared device',
                            created_by=admin_user
                        )
                        issues_fixed += 1
                
                self.stdout.write(self.style.SUCCESS(f'  ✅ Fixed {shared_without_usage.count()} devices'))
        
        # Summary
        self.stdout.write('')
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS('✅ No data integrity issues found!'))
        else:
            if fix_issues:
                self.stdout.write(
                    self.style.SUCCESS(f'🔧 Fixed {issues_fixed} out of {issues_found} issues found')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Found {issues_found} data integrity issues')
                )
                self.stdout.write('Run with --fix to automatically fix these issues')
        
        self.stdout.write('')
        self.stdout.write('=== INTEGRITY CHECK COMPLETE ===')