from django.core.management.base import BaseCommand
from core.models import AuditLog


class Command(BaseCommand):
    help = 'Fix inconsistent audit log action names'

    def handle(self, *args, **options):
        self.stdout.write('Starting audit log action cleanup...')
        
        # Fix 'updated' to 'update'
        updated_count = AuditLog.objects.filter(action='updated').update(action='update')
        self.stdout.write(f'Fixed {updated_count} "updated" actions to "update"')
        
        # Fix 'created' to 'create'
        created_count = AuditLog.objects.filter(action='created').update(action='create')
        self.stdout.write(f'Fixed {created_count} "created" actions to "create"')
        
        # Fix 'deleted' to 'delete'
        deleted_count = AuditLog.objects.filter(action='deleted').update(action='delete')
        self.stdout.write(f'Fixed {deleted_count} "deleted" actions to "delete"')
        
        total_fixed = updated_count + created_count + deleted_count
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {total_fixed} audit log entries')
        )
        
        # Show current action distribution
        self.stdout.write('\nCurrent action distribution:')
        actions = AuditLog.objects.values('action').distinct()
        for action in actions:
            count = AuditLog.objects.filter(action=action['action']).count()
            self.stdout.write(f'  {action["action"]}: {count}')