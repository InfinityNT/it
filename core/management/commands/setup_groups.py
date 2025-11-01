from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import User
from devices.models import Device
from employees.models import Employee
from assignments.models import Assignment


class Command(BaseCommand):
    help = 'Create Django groups and permissions for the IT Device Management system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Django groups and permissions...')
        
        # Create custom permissions
        self.create_custom_permissions()
        
        # Create groups
        self.create_groups()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up groups and permissions!')
        )

    def create_custom_permissions(self):
        """Create custom permissions for the application"""
        
        # Get content types for our models
        user_ct = ContentType.objects.get_for_model(User)
        device_ct = ContentType.objects.get_for_model(Device)
        employee_ct = ContentType.objects.get_for_model(Employee)
        assignment_ct = ContentType.objects.get_for_model(Assignment)
        
        # Define custom permissions
        permissions = [
            # Device permissions
            ('can_view_devices', 'Can view devices', device_ct),
            ('can_modify_devices', 'Can add/edit devices', device_ct),
            ('can_delete_devices', 'Can delete devices', device_ct),
            ('can_assign_devices', 'Can assign/unassign devices', device_ct),
            
            # Employee permissions
            ('can_view_employees', 'Can view employees', employee_ct),
            ('can_modify_employees', 'Can add/edit employees', employee_ct),
            ('can_delete_employees', 'Can delete employees', employee_ct),
            
            # User permissions
            ('can_view_users', 'Can view users', user_ct),
            ('can_modify_users', 'Can add/edit users', user_ct),
            ('can_delete_users', 'Can delete users', user_ct),
            
            # Assignment permissions
            ('can_view_assignments', 'Can view assignments', assignment_ct),
            ('can_modify_assignments', 'Can manage assignments', assignment_ct),
            ('can_approve_assignments', 'Can approve assignments', assignment_ct),
            
            # System permissions
            ('can_access_admin', 'Can access Django admin', user_ct),
            ('can_manage_system', 'Can manage system settings', user_ct),
            ('can_view_reports', 'Can view reports', user_ct),
            ('can_generate_reports', 'Can generate reports', user_ct),
        ]
        
        # Create permissions
        for codename, name, content_type in permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=content_type
            )
            if created:
                self.stdout.write(f'Created permission: {name}')

    def create_groups(self):
        """Create groups with appropriate permissions"""
        
        # Define groups and their permissions
        groups_permissions = {
            'Managers': [
                # Full access to everything
                'can_view_devices', 'can_modify_devices', 'can_delete_devices', 'can_assign_devices',
                'can_view_employees', 'can_modify_employees', 'can_delete_employees',
                'can_view_users', 'can_modify_users', 'can_delete_users',
                'can_view_assignments', 'can_modify_assignments', 'can_approve_assignments',
                'can_access_admin', 'can_manage_system',
                'can_view_reports', 'can_generate_reports',
            ],
            'Staff': [
                # Can manage devices and assignments, limited user management
                'can_view_devices', 'can_modify_devices', 'can_assign_devices',
                'can_view_employees', 'can_modify_employees',
                'can_view_users', 'can_modify_users',
                'can_view_assignments', 'can_modify_assignments',
                'can_view_reports', 'can_generate_reports',
            ],
            'Viewers': [
                # Read-only access
                'can_view_devices',
                'can_view_employees',
                'can_view_assignments',
                'can_view_reports',
            ],
        }
        
        # Create groups and assign permissions
        for group_name, permission_codenames in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions to group
            for codename in permission_codenames:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission not found: {codename}')
                    )
            
            self.stdout.write(
                f'Assigned {len(permission_codenames)} permissions to {group_name}'
            )

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-users',
            action='store_true',
            help='Assign existing users to appropriate groups based on their current role'
        )
        
        if parser.parse_known_args()[0].assign_users:
            self.assign_existing_users()

    def assign_existing_users(self):
        """Assign existing users to appropriate groups based on their current permissions"""
        self.stdout.write('Role field has been removed. Users should be assigned to groups manually or based on their existing permissions.')
        self.stdout.write('Available groups: Managers, Staff, Viewers')
        
        # Assign superusers to Managers group
        try:
            managers_group = Group.objects.get(name='Managers')
            for user in User.objects.filter(is_superuser=True):
                user.groups.add(managers_group)
                self.stdout.write(f'Assigned superuser {user.username} to Managers')
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('Managers group not found'))
        
        # Assign staff users to Staff group
        try:
            staff_group = Group.objects.get(name='Staff')
            for user in User.objects.filter(is_staff=True, is_superuser=False):
                user.groups.add(staff_group)
                self.stdout.write(f'Assigned staff user {user.username} to Staff')
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('Staff group not found'))
        
        # Assign remaining users to Viewers group
        try:
            viewers_group = Group.objects.get(name='Viewers')
            for user in User.objects.filter(is_staff=False, is_superuser=False, groups__isnull=True):
                user.groups.add(viewers_group)
                self.stdout.write(f'Assigned regular user {user.username} to Viewers')
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING('Viewers group not found'))