from django.core.management.base import BaseCommand
from core.models import User, UserQuickAction


class Command(BaseCommand):
    help = 'Setup default quick actions for all users based on their roles'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default quick actions for users...')
        
        
        users_updated = 0
        
        for user in User.objects.all():
            # Get default actions based on user's permissions
            user_actions = self.get_default_actions_for_user(user)
            
            if user_actions:
                # Clear existing quick actions for this user
                UserQuickAction.objects.filter(user=user).delete()
                
                # Create default quick actions
                actions_to_create = []
                for action_code, display_order in user_actions:
                    actions_to_create.append(UserQuickAction(
                        user=user,
                        action_code=action_code,
                        display_order=display_order,
                        is_enabled=True
                    ))
                
                UserQuickAction.objects.bulk_create(actions_to_create)
                users_updated += 1
                
                # Determine user role for display
                role_display = "Viewer"
                if user.can_manage_system_settings:
                    role_display = "Manager"
                elif user.can_modify_assignments:
                    role_display = "Staff"
                
                self.stdout.write(
                    f'✓ Set up {len(actions_to_create)} quick actions for {user.username} ({role_display})'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully set up default quick actions for {users_updated} users!')
        )

    def get_default_actions_for_user(self, user):
        """Get default actions for a user based on their individual permissions"""
        actions_to_add = []
        display_order = 0
        
        # Check each action individually based on required permissions
        action_permissions = {
            'add_device': 'devices.can_modify_devices',
            'assign_device': 'devices.can_assign_devices',
            'return_device': 'devices.can_assign_devices',
            'add_user': 'core.can_modify_users',
            'add_employee': 'employees.can_modify_employees',
            'quick_search': None,  # Available to all authenticated users
            'generate_report': 'core.can_view_reports',
            'approvals': 'assignments.can_modify_assignments',
        }
        
        for action_code, required_permission in action_permissions.items():
            if required_permission is None or user.has_perm(required_permission):
                actions_to_add.append((action_code, display_order))
                display_order += 1
        
        return actions_to_add