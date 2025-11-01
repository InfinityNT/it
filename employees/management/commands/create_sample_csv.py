from django.core.management.base import BaseCommand
import csv
import os


class Command(BaseCommand):
    help = 'Create sample CSV file for employee import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='sample_employees.csv',
            help='Output file path (default: sample_employees.csv)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        # Sample employee data
        sample_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@company.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_id': 'EMP001',
                'department': 'Information Technology',
                'job_title': 'Software Engineer',
                'hire_date': '2023-01-15',
                'work_phone': '555-0123',
                'mobile_phone': '555-0124',
                'office_location': 'Building A - Floor 3'
            },
            {
                'username': 'jane.smith',
                'email': 'jane.smith@company.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_id': 'EMP002',
                'department': 'Human Resources',
                'job_title': 'HR Manager',
                'hire_date': '2022-03-10',
                'work_phone': '555-0125',
                'mobile_phone': '555-0126',
                'office_location': 'Building A - Floor 2'
            },
            {
                'username': 'mike.johnson',
                'email': 'mike.johnson@company.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'employee_id': 'EMP003',
                'department': 'Finance',
                'job_title': 'Senior Accountant',
                'hire_date': '2021-06-20',
                'work_phone': '555-0127',
                'mobile_phone': '555-0128',
                'office_location': 'Building A - Floor 5'
            },
            {
                'username': 'sarah.wilson',
                'email': 'sarah.wilson@company.com',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'employee_id': 'EMP004',
                'department': 'Marketing',
                'job_title': 'Marketing Manager',
                'hire_date': '2022-09-05',
                'work_phone': '555-0129',
                'mobile_phone': '555-0130',
                'office_location': 'Building B - Floor 2'
            },
            {
                'username': 'david.brown',
                'email': 'david.brown@company.com',
                'first_name': 'David',
                'last_name': 'Brown',
                'employee_id': 'EMP005',
                'department': 'Sales',
                'job_title': 'Sales Manager',
                'hire_date': '2020-11-12',
                'work_phone': '555-0131',
                'mobile_phone': '555-0132',
                'office_location': 'Building B - Floor 3'
            }
        ]
        
        # Create CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = sample_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'Sample CSV file created: {os.path.abspath(output_file)}')
        )
        
        # Show usage instructions
        self.stdout.write('\n' + self.style.WARNING('Usage Instructions:'))
        self.stdout.write('1. Edit the CSV file with your employee data')
        self.stdout.write('2. Run import command:')
        self.stdout.write(f'   python manage.py import_from_ad --source csv --file {output_file}')
        self.stdout.write('3. Use --dry-run to preview changes first:')
        self.stdout.write(f'   python manage.py import_from_ad --source csv --file {output_file} --dry-run')
        self.stdout.write('4. Use --update-existing to update existing employees:')
        self.stdout.write(f'   python manage.py import_from_ad --source csv --file {output_file} --update-existing')
        
        self.stdout.write('\n' + self.style.WARNING('CSV Format:'))
        self.stdout.write('Required columns: username, email, first_name, last_name')
        self.stdout.write('Optional columns: employee_id, department, job_title, hire_date, work_phone, mobile_phone, office_location')
        
        self.stdout.write('\n' + self.style.WARNING('Active Directory Import:'))
        self.stdout.write('1. Install ldap3: pip install ldap3')
        self.stdout.write('2. Configure AD settings in settings.py (see employees/ad_config.py)')
        self.stdout.write('3. Run: python manage.py import_from_ad --source ad --ad-server ldap://your-server.com --ad-username user@domain.com --ad-password password')