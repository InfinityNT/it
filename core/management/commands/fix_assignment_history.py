from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from devices.models import Device, DeviceHistory
from assignments.models import Assignment
from employees.models import Employee
from core.models import User


class Command(BaseCommand):
    help = 'Fix assignment history inconsistencies for all devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write('Analyzing assignment data...')

        # Find inconsistencies
        issues = self.analyze_assignment_data(verbose)
        
        if not any(issues.values()):
            self.stdout.write(self.style.SUCCESS('✅ No assignment inconsistencies found!'))
            return

        self.stdout.write(f'Found inconsistencies in {sum(len(v) if isinstance(v, list) else len(v) for v in issues.values())} cases')

        if dry_run:
            self.stdout.write('Would fix the following issues:')
            self.show_issues(issues)
        else:
            self.stdout.write('Fixing assignment inconsistencies...')
            fixed_count = self.fix_assignment_inconsistencies(issues, verbose)
            self.stdout.write(self.style.SUCCESS(f'✅ Fixed {fixed_count} assignment issues'))

    def analyze_assignment_data(self, verbose=False):
        """Analyze current assignment data inconsistencies"""
        issues = {}

        # 1. Devices marked as assigned but no active Assignment record
        devices_assigned_no_record = Device.objects.filter(
            status='assigned',
            assigned_to__isnull=False
        ).exclude(
            id__in=Assignment.objects.filter(status='active').values_list('device_id', flat=True)
        )
        issues['devices_assigned_no_record'] = devices_assigned_no_record

        # 2. Active Assignment records but device not marked as assigned
        active_assignments_device_not_assigned = Assignment.objects.filter(
            status='active'
        ).exclude(
            device__status='assigned'
        )
        issues['active_assignments_device_not_assigned'] = active_assignments_device_not_assigned

        # 3. Device assigned_to doesn't match active Assignment employee
        mismatched_assignments = []
        for assignment in Assignment.objects.filter(status='active'):
            if assignment.device.assigned_to != assignment.employee:
                mismatched_assignments.append(assignment)
        issues['mismatched_assignments'] = mismatched_assignments

        # 4. Multiple active assignments for same device
        devices_multiple_active = {}
        for assignment in Assignment.objects.filter(status='active'):
            device_id = assignment.device.id
            if device_id in devices_multiple_active:
                devices_multiple_active[device_id].append(assignment)
            else:
                devices_multiple_active[device_id] = [assignment]
        
        multiple_active = {k: v for k, v in devices_multiple_active.items() if len(v) > 1}
        issues['multiple_active'] = multiple_active

        if verbose:
            self.show_issues(issues)

        return issues

    def show_issues(self, issues):
        """Display found issues"""
        if issues['devices_assigned_no_record']:
            self.stdout.write(f"• {len(issues['devices_assigned_no_record'])} devices assigned but missing Assignment records")
            
        if issues['active_assignments_device_not_assigned']:
            self.stdout.write(f"• {len(issues['active_assignments_device_not_assigned'])} active assignments with unassigned devices")
            
        if issues['mismatched_assignments']:
            self.stdout.write(f"• {len(issues['mismatched_assignments'])} assignments with mismatched employees")
            
        if issues['multiple_active']:
            self.stdout.write(f"• {len(issues['multiple_active'])} devices with multiple active assignments")

    def fix_assignment_inconsistencies(self, issues, verbose=False):
        """Fix all identified assignment inconsistencies"""
        fixed_count = 0
        
        with transaction.atomic():
            # Fix 1: Create Assignment records for devices that are assigned but missing records
            for device in issues['devices_assigned_no_record']:
                try:
                    assigned_by = device.created_by or User.objects.filter(is_superuser=True).first() or User.objects.first()
                    
                    Assignment.objects.create(
                        device=device,
                        employee=device.assigned_to,
                        assigned_by=assigned_by,
                        assigned_date=device.assigned_date or timezone.now(),
                        status='active',
                        condition_at_assignment=device.condition,
                        notes='Assignment record created during data migration'
                    )
                    
                    if verbose:
                        self.stdout.write(f'  ✓ Created Assignment record for {device.asset_tag}')
                    fixed_count += 1
                    
                    # Create corresponding DeviceHistory record if it doesn't exist
                    if not DeviceHistory.objects.filter(device=device, action='assigned', new_employee=device.assigned_to).exists():
                        DeviceHistory.objects.create(
                            device=device,
                            action='assigned',
                            new_employee=device.assigned_to,
                            new_status='assigned',
                            previous_status='available',
                            notes='History record created during data migration',
                            created_by=assigned_by
                        )
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to create Assignment for {device.asset_tag}: {e}'))

            # Fix 2: Update device status for active assignments where device is not marked as assigned
            for assignment in issues['active_assignments_device_not_assigned']:
                try:
                    assignment.device.status = 'assigned'
                    assignment.device.assigned_to = assignment.employee
                    assignment.device.assigned_date = assignment.assigned_date
                    assignment.device.save()
                    
                    if verbose:
                        self.stdout.write(f'  ✓ Updated {assignment.device.asset_tag} status to assigned')
                    fixed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to update {assignment.device.asset_tag}: {e}'))

            # Fix 3: Resolve mismatched employee assignments
            for assignment in issues['mismatched_assignments']:
                try:
                    assignment.device.assigned_to = assignment.employee
                    assignment.device.save()
                    
                    if verbose:
                        self.stdout.write(f'  ✓ Fixed employee mismatch for {assignment.device.asset_tag}')
                    fixed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to update {assignment.device.asset_tag}: {e}'))

            # Fix 4: Resolve multiple active assignments
            for device_id, assignments in issues['multiple_active'].items():
                try:
                    device = Device.objects.get(id=device_id)
                    assignments.sort(key=lambda a: a.assigned_date, reverse=True)
                    latest_assignment = assignments[0]
                    older_assignments = assignments[1:]
                    
                    # Update device to match latest assignment
                    device.assigned_to = latest_assignment.employee
                    device.assigned_date = latest_assignment.assigned_date
                    device.save()
                    
                    # Mark older assignments as returned
                    for old_assignment in older_assignments:
                        old_assignment.status = 'returned'
                        old_assignment.actual_return_date = latest_assignment.assigned_date
                        old_assignment.return_notes = 'Automatically closed during data migration'
                        old_assignment.save()
                    
                    if verbose:
                        self.stdout.write(f'  ✓ Resolved multiple assignments for {device.asset_tag}')
                    fixed_count += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to resolve multiple assignments for device {device_id}: {e}'))

        return fixed_count