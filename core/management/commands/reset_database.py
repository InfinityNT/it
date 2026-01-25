"""
reset_database.py - Configurable database reset command

Usage:
    python manage.py reset_database
    python manage.py reset_database --keep-users
    python manage.py reset_database --keep-users --keep-reference-data
    python manage.py reset_database --keep-users --keep-reference-data --keep-audit-logs
    python manage.py reset_database --no-confirm
    python manage.py reset_database --regenerate
    python manage.py reset_database --keep-users --regenerate
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction, connection
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset database with configurable data preservation options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Preserve User accounts (including superusers)'
        )
        parser.add_argument(
            '--keep-reference-data',
            action='store_true',
            help='Preserve manufacturers, vendors, categories, departments, job titles'
        )
        parser.add_argument(
            '--keep-audit-logs',
            action='store_true',
            help='Preserve AuditLog records'
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Skip confirmation prompt (for CI/testing)'
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='After reset, run data generation commands'
        )
        parser.add_argument(
            '--regenerate-count',
            type=int,
            default=50,
            help='Number of records to generate when using --regenerate (default: 50)'
        )

    def handle(self, *args, **options):
        keep_users = options['keep_users']
        keep_reference_data = options['keep_reference_data']
        keep_audit_logs = options['keep_audit_logs']
        no_confirm = options['no_confirm']
        regenerate = options['regenerate']
        regenerate_count = options['regenerate_count']

        # Show what will be deleted
        self._display_deletion_plan(keep_users, keep_reference_data, keep_audit_logs)

        # Confirm unless --no-confirm is set
        if not no_confirm:
            confirm = input('\nType "yes" to proceed with database reset: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Starting database reset...'))

        try:
            with transaction.atomic():
                self._perform_reset(keep_users, keep_reference_data, keep_audit_logs)

            self.stdout.write(self.style.SUCCESS('Database reset completed successfully!'))

            if regenerate:
                self.stdout.write('')
                self.stdout.write('Regenerating data...')
                self._regenerate_data(regenerate_count, keep_reference_data)
                self.stdout.write(self.style.SUCCESS('Data regeneration completed!'))

        except Exception as e:
            raise CommandError(f'Database reset failed: {str(e)}')

    def _display_deletion_plan(self, keep_users, keep_reference_data, keep_audit_logs):
        """Display what will be deleted"""
        from approvals.models import ApprovalComment, ApprovalRequest
        from assignments.models import Assignment
        from devices.models import Device, DeviceHistory, DeviceModel, DeviceCategory, DeviceManufacturer, DeviceVendor
        from employees.models import Employee, Department, JobTitle
        from core.models import AuditLog, UserQuickAction, Location
        from reports.models import ReportTemplate, ReportGeneration

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=== DATABASE RESET PLAN ==='))
        self.stdout.write('')

        # Always deleted
        self.stdout.write('WILL BE DELETED:')
        self.stdout.write(f'  - ApprovalComment: {ApprovalComment.objects.count()} records')
        self.stdout.write(f'  - ApprovalRequest: {ApprovalRequest.objects.count()} records')
        self.stdout.write(f'  - Assignment: {Assignment.objects.count()} records')
        self.stdout.write(f'  - DeviceHistory: {DeviceHistory.objects.count()} records')
        self.stdout.write(f'  - Device: {Device.objects.count()} records')
        self.stdout.write(f'  - ReportGeneration: {ReportGeneration.objects.count()} records')
        self.stdout.write(f'  - ReportTemplate: {ReportTemplate.objects.count()} records')

        if not keep_reference_data:
            self.stdout.write(f'  - DeviceModel: {DeviceModel.objects.count()} records')
            self.stdout.write(f'  - DeviceCategory: {DeviceCategory.objects.count()} records')
            self.stdout.write(f'  - DeviceManufacturer: {DeviceManufacturer.objects.count()} records')
            self.stdout.write(f'  - DeviceVendor: {DeviceVendor.objects.count()} records')
            self.stdout.write(f'  - Employee: {Employee.objects.count()} records')
            self.stdout.write(f'  - JobTitle: {JobTitle.objects.count()} records')
            self.stdout.write(f'  - Department: {Department.objects.count()} records')
            self.stdout.write(f'  - Location: {Location.objects.count()} records')

        if not keep_users:
            self.stdout.write(f'  - UserQuickAction: {UserQuickAction.objects.count()} records')
            self.stdout.write(f'  - User: {User.objects.count()} records')

        if not keep_audit_logs:
            self.stdout.write(f'  - AuditLog: {AuditLog.objects.count()} records')

        # Preserved
        self.stdout.write('')
        self.stdout.write('WILL BE PRESERVED:')
        preserved = []
        if keep_users:
            preserved.append(f'  - User: {User.objects.count()} records')
            preserved.append(f'  - UserQuickAction: {UserQuickAction.objects.count()} records')
        if keep_reference_data:
            preserved.append(f'  - DeviceModel: {DeviceModel.objects.count()} records')
            preserved.append(f'  - DeviceCategory: {DeviceCategory.objects.count()} records')
            preserved.append(f'  - DeviceManufacturer: {DeviceManufacturer.objects.count()} records')
            preserved.append(f'  - DeviceVendor: {DeviceVendor.objects.count()} records')
            preserved.append(f'  - Department: {Department.objects.count()} records')
            preserved.append(f'  - JobTitle: {JobTitle.objects.count()} records')
            preserved.append(f'  - Location: {Location.objects.count()} records')
        if keep_audit_logs:
            preserved.append(f'  - AuditLog: {AuditLog.objects.count()} records')

        if preserved:
            for item in preserved:
                self.stdout.write(item)
        else:
            self.stdout.write('  (nothing - full reset)')

    def _perform_reset(self, keep_users, keep_reference_data, keep_audit_logs):
        """Perform the actual database reset with proper deletion order"""
        from approvals.models import ApprovalComment, ApprovalRequest
        from assignments.models import Assignment
        from devices.models import Device, DeviceHistory, DeviceModel, DeviceCategory, DeviceManufacturer, DeviceVendor
        from employees.models import Employee, Department, JobTitle
        from core.models import AuditLog, UserQuickAction, Location
        from reports.models import ReportTemplate, ReportGeneration

        # DELETION ORDER (respecting foreign key constraints):

        # 1. ApprovalComment (FK to ApprovalRequest)
        self.stdout.write('  Deleting ApprovalComment...')
        ApprovalComment.objects.all().delete()

        # 2. Assignments (FK to ApprovalRequest, Device, Employee)
        self.stdout.write('  Deleting Assignment...')
        Assignment.objects.all().delete()

        # 3. ApprovalRequest (FK to Device via M2M)
        self.stdout.write('  Deleting ApprovalRequest...')
        ApprovalRequest.objects.all().delete()

        # 4. DeviceHistory (FK to Device, Employee)
        self.stdout.write('  Deleting DeviceHistory...')
        DeviceHistory.objects.all().delete()

        # 5. Device (FK to DeviceModel, Employee)
        self.stdout.write('  Deleting Device...')
        Device.objects.all().delete()

        # 6. ReportGeneration (FK to ReportTemplate)
        self.stdout.write('  Deleting ReportGeneration...')
        ReportGeneration.objects.all().delete()

        # 7. ReportTemplate
        self.stdout.write('  Deleting ReportTemplate...')
        ReportTemplate.objects.all().delete()

        # Conditional deletions
        if not keep_reference_data:
            # 8. DeviceModel (FK to DeviceCategory)
            self.stdout.write('  Deleting DeviceModel...')
            DeviceModel.objects.all().delete()

            # 9. DeviceCategory, DeviceManufacturer, DeviceVendor
            self.stdout.write('  Deleting DeviceCategory...')
            DeviceCategory.objects.all().delete()
            self.stdout.write('  Deleting DeviceManufacturer...')
            DeviceManufacturer.objects.all().delete()
            self.stdout.write('  Deleting DeviceVendor...')
            DeviceVendor.objects.all().delete()

            # 10. Employee (handle user links)
            if keep_users:
                # Unlink employees from users before deleting
                self.stdout.write('  Unlinking Employees from Users...')
                Employee.objects.all().update(system_user=None)
                User.objects.all().update(linked_employee=None)

            self.stdout.write('  Deleting Employee...')
            Employee.objects.all().delete()

            # 11. JobTitle (FK to Department)
            self.stdout.write('  Deleting JobTitle...')
            JobTitle.objects.all().delete()

            # 12. Department
            self.stdout.write('  Deleting Department...')
            Department.objects.all().delete()

            # 13. Location
            self.stdout.write('  Deleting Location...')
            Location.objects.all().delete()

        if not keep_users:
            # 14. UserQuickAction (FK to User)
            self.stdout.write('  Deleting UserQuickAction...')
            UserQuickAction.objects.all().delete()

            # 15. User
            self.stdout.write('  Deleting User...')
            User.objects.all().delete()

        if not keep_audit_logs:
            # 16. AuditLog
            self.stdout.write('  Deleting AuditLog...')
            AuditLog.objects.all().delete()

        # Reset sequences for SQLite
        if connection.vendor == 'sqlite':
            self._reset_sqlite_sequences()

    def _reset_sqlite_sequences(self):
        """Reset SQLite auto-increment sequences"""
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                if not table_name.startswith('django_') and not table_name.startswith('auth_') and not table_name.startswith('sqlite_'):
                    try:
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}';")
                    except Exception:
                        pass  # Table might not have auto-increment

    def _regenerate_data(self, count, keep_reference_data):
        """Regenerate sample data after reset"""
        if not keep_reference_data:
            self.stdout.write('  Running create_predefined_data...')
            call_command('create_predefined_data')

            self.stdout.write('  Running populate_mock_data...')
            call_command('populate_mock_data', count=count)

        self.stdout.write('  Running generate_sample_devices...')
        call_command('generate_sample_devices', count=count)

        self.stdout.write('  Running setup_groups...')
        call_command('setup_groups')
