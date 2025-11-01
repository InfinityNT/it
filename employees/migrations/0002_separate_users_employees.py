# Generated manually to separate Users and Employees
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employees', '0001_initial'),
    ]

    operations = [
        # Step 1: Add new fields with nullable/default values
        migrations.AddField(
            model_name='employee',
            name='first_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employee',
            name='last_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employee',
            name='email',
            field=models.EmailField(default='temp@example.com', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employee',
            name='manager_employee_id',
            field=models.CharField(blank=True, help_text="Manager's employee ID", max_length=50),
        ),
        
        # Step 2: Add the new system_user field (nullable)
        migrations.AddField(
            model_name='employee',
            name='system_user',
            field=models.OneToOneField(
                blank=True, 
                help_text='Link to system user account if employee has portal access', 
                null=True, 
                on_delete=django.db.models.deletion.SET_NULL, 
                related_name='employee_profile', 
                to=settings.AUTH_USER_MODEL
            ),
        ),
        
        # Step 3: Update Department model
        migrations.AddField(
            model_name='department',
            name='manager_employee_id',
            field=models.CharField(blank=True, help_text="Manager's employee ID", max_length=50),
        ),
        
        # Step 4: Populate new fields from existing User data
        migrations.RunPython(
            code=lambda apps, schema_editor: migrate_user_data_to_employee_fields(apps, schema_editor),
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 5: Make email field unique
        migrations.AlterField(
            model_name='employee',
            name='email',
            field=models.EmailField(unique=True),
        ),
        
        # Step 6: Remove old User foreign key and manager field from Department
        migrations.RemoveField(
            model_name='employee',
            name='user',
        ),
        migrations.RemoveField(
            model_name='employee',
            name='manager',
        ),
        migrations.RemoveField(
            model_name='department',
            name='manager',
        ),
    ]


def migrate_user_data_to_employee_fields(apps, schema_editor):
    """Migrate data from User fields to Employee fields"""
    Employee = apps.get_model('employees', 'Employee')
    
    for employee in Employee.objects.all():
        if hasattr(employee, 'user') and employee.user:
            # Copy user data to employee fields
            employee.first_name = employee.user.first_name or 'Unknown'
            employee.last_name = employee.user.last_name or 'User'
            employee.email = employee.user.email or f'user{employee.user.id}@example.com'
            
            # Keep reference to system user
            employee.system_user = employee.user
            
            employee.save()
        else:
            # Handle employees without users
            employee.first_name = 'Unknown'
            employee.last_name = 'Employee' 
            employee.email = f'employee{employee.employee_id}@example.com'
            employee.save()