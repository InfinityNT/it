"""
Django management command to set up proper authentication system.
Follows Django best practices for permission setup.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.authtoken.models import Token
from core.models import User


class Command(BaseCommand):
    help = 'Set up authentication system with proper permissions and groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Create a test user with API token',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username for test user (default: testuser)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for test user (default: testpass123)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Setting up authentication system...')
        )

        # Create groups
        self.create_permission_groups()
        
        # Set up custom permissions
        self.setup_custom_permissions()
        
        # Create test user if requested
        if options['create_test_user']:
            self.create_test_user(options['username'], options['password'])
        
        # Create API token for admin user
        self.create_admin_token()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Authentication system setup complete!')
        )

    def create_permission_groups(self):
        """Create standard permission groups"""
        groups_config = {
            'User Managers': [
                'core.add_user',
                'core.change_user',
                'core.delete_user',
                'core.view_user',
            ],
            'Device Managers': [
                'devices.add_device',
                'devices.change_device',
                'devices.delete_device',
                'devices.view_device',
                'devices.add_devicecategory',
                'devices.change_devicecategory',
            ],
            'Assignment Managers': [
                'assignments.add_assignment',
                'assignments.change_assignment',
                'assignments.delete_assignment',
                'assignments.view_assignment',
            ],
            'Approvers': [
                'approvals.add_approval',
                'approvals.change_approval',
                'approvals.view_approval',
            ],
            'Report Viewers': [
                'reports.view_report',
            ],
            'Maintenance Staff': [
                'maintenance.add_maintenancerequest',
                'maintenance.change_maintenancerequest',
                'maintenance.view_maintenancerequest',
            ],
            'Employees': [
                'employees.view_employee',
                'assignments.view_assignment',
                'devices.view_device',
            ],
        }

        for group_name, permission_codenames in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                self.stdout.write(f'✅ Created group: {group_name}')
            
            # Add permissions to group
            for codename in permission_codenames:
                try:
                    app_label, permission_name = codename.split('.')
                    permission = Permission.objects.get(
                        codename=permission_name,
                        content_type__app_label=app_label
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Permission not found: {codename}')
                    )

    def setup_custom_permissions(self):
        """Set up custom permissions for the project"""
        custom_permissions = [
            ('core', 'User', 'can_manage_users', 'Can manage users'),
            ('core', 'User', 'can_view_audit_logs', 'Can view audit logs'),
            ('devices', 'Device', 'can_manage_devices', 'Can manage devices'),
            ('assignments', 'Assignment', 'can_manage_assignments', 'Can manage assignments'),
            ('approvals', 'Approval', 'can_approve_requests', 'Can approve requests'),
            ('reports', 'User', 'can_view_reports', 'Can view reports'),
            ('maintenance', 'MaintenanceRequest', 'can_manage_maintenance', 'Can manage maintenance'),
        ]

        for app_label, model_name, codename, name in custom_permissions:
            try:
                content_type = ContentType.objects.get(
                    app_label=app_label,
                    model=model_name.lower()
                )
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': name}
                )
                if created:
                    self.stdout.write(f'✅ Created permission: {codename}')
            except ContentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Content type not found: {app_label}.{model_name}')
                )

    def create_test_user(self, username, password):
        """Create a test user with API access"""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f'✅ Created test user: {username}')
        else:
            self.stdout.write(f'ℹ️  Test user already exists: {username}')
        
        # Add user to all groups for testing
        user.groups.set(Group.objects.all())
        user.user_permissions.set(Permission.objects.all())
        
        # Create API token
        token, created = Token.objects.get_or_create(user=user)
        if created:
            self.stdout.write(f'✅ Created API token for {username}: {token.key}')
        else:
            self.stdout.write(f'ℹ️  API token exists for {username}: {token.key}')

    def create_admin_token(self):
        """Create API token for admin user"""
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                token, created = Token.objects.get_or_create(user=admin_user)
                if created:
                    self.stdout.write(f'✅ Created API token for admin: {token.key}')
                else:
                    self.stdout.write(f'ℹ️  API token exists for admin: {token.key}')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  No admin user found')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin token: {str(e)}')
            )