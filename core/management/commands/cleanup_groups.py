from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core.models import User


class Command(BaseCommand):
    help = 'Remove obsolete groups and reassign users to Managers, Staff, or Viewers'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up obsolete groups...')

        # Groups to keep
        valid_groups = ['Managers', 'Staff', 'Viewers']

        # Groups to delete
        obsolete_groups = [
            'User Managers',
            'Device Managers',
            'Assignment Managers',
            'Approvers',
            'Report Viewers',
            'Maintenance Staff',
            'Employees'
        ]

        # Get reference groups for reassignment
        managers_group = Group.objects.get(name='Managers')
        staff_group = Group.objects.get(name='Staff')
        viewers_group = Group.objects.get(name='Viewers')

        # Process each obsolete group
        for group_name in obsolete_groups:
            try:
                group = Group.objects.get(name=group_name)
                users_in_group = group.user_set.all()

                if users_in_group.exists():
                    self.stdout.write(f'Found {users_in_group.count()} users in {group_name}')

                    # Reassign users based on their role
                    for user in users_in_group:
                        # Check if user already has a valid group
                        user_valid_groups = user.groups.filter(name__in=valid_groups)

                        if not user_valid_groups.exists():
                            # Assign based on user's privileges
                            if user.is_superuser:
                                user.groups.add(managers_group)
                                self.stdout.write(f'  → Reassigned {user.username} to Managers (superuser)')
                            elif user.is_staff:
                                user.groups.add(staff_group)
                                self.stdout.write(f'  → Reassigned {user.username} to Staff')
                            else:
                                user.groups.add(viewers_group)
                                self.stdout.write(f'  → Reassigned {user.username} to Viewers')
                        else:
                            self.stdout.write(f'  → {user.username} already in {user_valid_groups.first().name}')

                # Delete the obsolete group
                group.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ Deleted group: {group_name}'))

            except Group.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Group "{group_name}" not found, skipping'))

        # Show final group count
        remaining_groups = Group.objects.all()
        self.stdout.write('\n' + self.style.SUCCESS(f'Cleanup complete! Remaining groups ({remaining_groups.count()}):'))
        for group in remaining_groups:
            user_count = group.user_set.count()
            self.stdout.write(f'  - {group.name}: {user_count} users')
