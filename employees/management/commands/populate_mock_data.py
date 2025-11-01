from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta
import random

from core.models import User
from employees.models import Employee, Department, JobTitle


class Command(BaseCommand):
    help = 'Populate database with mock employee data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of employees to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing employee data before creating new'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            self.stdout.write('Clearing existing employee data...')
            Employee.objects.all().delete()
            User.objects.exclude(username='admin').delete()
            Department.objects.all().delete()
            JobTitle.objects.all().delete()

        with transaction.atomic():
            self.create_departments()
            self.create_job_titles()
            self.create_employees(count)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} employees with mock data')
        )

    def create_departments(self):
        """Create company departments"""
        departments_data = [
            {
                'name': 'Information Technology',
                'code': 'IT',
                'description': 'Manages all technology infrastructure and systems',
                'budget_code': 'IT-001',
                'location': 'Building A - Floor 3'
            },
            {
                'name': 'Human Resources',
                'code': 'HR',
                'description': 'Handles employee relations and organizational development',
                'budget_code': 'HR-001',
                'location': 'Building A - Floor 2'
            },
            {
                'name': 'Finance',
                'code': 'FIN',
                'description': 'Manages financial operations and reporting',
                'budget_code': 'FIN-001',
                'location': 'Building A - Floor 5'
            },
            {
                'name': 'Marketing',
                'code': 'MKT',
                'description': 'Handles marketing and communications',
                'budget_code': 'MKT-001',
                'location': 'Building B - Floor 2'
            },
            {
                'name': 'Sales',
                'code': 'SAL',
                'description': 'Manages sales operations and customer relations',
                'budget_code': 'SAL-001',
                'location': 'Building B - Floor 3'
            },
            {
                'name': 'Operations',
                'code': 'OPS',
                'description': 'Oversees day-to-day operations',
                'budget_code': 'OPS-001',
                'location': 'Building A - Floor 1'
            },
            {
                'name': 'Legal',
                'code': 'LEG',
                'description': 'Handles legal affairs and compliance',
                'budget_code': 'LEG-001',
                'location': 'Building A - Floor 4'
            },
            {
                'name': 'Customer Service',
                'code': 'CS',
                'description': 'Provides customer support and service',
                'budget_code': 'CS-001',
                'location': 'Building C - Floor 1'
            }
        ]

        for dept_data in departments_data:
            department, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'Created department: {department.name}')

    def create_job_titles(self):
        """Create job titles for each department"""
        job_titles_data = {
            'IT': [
                'IT Director', 'Senior Software Engineer', 'Software Engineer', 
                'Junior Software Engineer', 'System Administrator', 'Database Administrator',
                'Network Engineer', 'Security Analyst', 'DevOps Engineer', 'IT Support Specialist'
            ],
            'HR': [
                'HR Director', 'HR Manager', 'HR Specialist', 'Recruiter', 
                'Benefits Administrator', 'Training Coordinator', 'HR Assistant'
            ],
            'FIN': [
                'CFO', 'Finance Director', 'Senior Accountant', 'Accountant', 
                'Financial Analyst', 'Accounts Payable Specialist', 'Accounts Receivable Specialist'
            ],
            'MKT': [
                'Marketing Director', 'Marketing Manager', 'Digital Marketing Specialist', 
                'Content Writer', 'Graphic Designer', 'Marketing Coordinator', 'SEO Specialist'
            ],
            'SAL': [
                'Sales Director', 'Sales Manager', 'Senior Sales Representative', 
                'Sales Representative', 'Sales Coordinator', 'Business Development Manager'
            ],
            'OPS': [
                'Operations Director', 'Operations Manager', 'Project Manager', 
                'Operations Coordinator', 'Process Analyst', 'Quality Assurance Specialist'
            ],
            'LEG': [
                'General Counsel', 'Senior Legal Counsel', 'Legal Counsel', 
                'Legal Assistant', 'Compliance Officer'
            ],
            'CS': [
                'Customer Service Director', 'Customer Service Manager', 
                'Senior Customer Service Representative', 'Customer Service Representative', 
                'Customer Success Specialist'
            ]
        }

        for dept_code, titles in job_titles_data.items():
            try:
                department = Department.objects.get(code=dept_code)
                for title in titles:
                    job_title, created = JobTitle.objects.get_or_create(
                        title=title,
                        department=department,
                        defaults={
                            'description': f'{title} in {department.name}',
                            'level': self.get_level_from_title(title)
                        }
                    )
                    if created:
                        self.stdout.write(f'Created job title: {job_title.title}')
            except Department.DoesNotExist:
                self.stdout.write(f'Department {dept_code} not found')

    def get_level_from_title(self, title):
        """Determine job level based on title"""
        title_lower = title.lower()
        if 'director' in title_lower or 'cfo' in title_lower or 'counsel' in title_lower:
            return 'Executive'
        elif 'manager' in title_lower or 'senior' in title_lower:
            return 'Senior'
        elif 'junior' in title_lower or 'assistant' in title_lower:
            return 'Junior'
        else:
            return 'Mid-level'

    def create_employees(self, count):
        """Create mock employees"""
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'James', 'Lisa',
            'Robert', 'Jennifer', 'William', 'Amanda', 'Richard', 'Jessica', 'Thomas',
            'Ashley', 'Christopher', 'Emily', 'Daniel', 'Melissa', 'Matthew', 'Michelle',
            'Anthony', 'Kimberly', 'Mark', 'Amy', 'Donald', 'Angela', 'Steven', 'Helen'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
            'Ramirez', 'Lewis', 'Robinson'
        ]

        domains = ['company.com', 'corp.com', 'business.com']
        phone_prefixes = ['555-0', '555-1', '555-2', '555-3']
        
        buildings = ['Building A', 'Building B', 'Building C']
        floors = ['Floor 1', 'Floor 2', 'Floor 3', 'Floor 4', 'Floor 5']

        departments = Department.objects.all()
        
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Create unique username
            username = f"{first_name.lower()}.{last_name.lower()}"
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            # Assign department and job title
            department = random.choice(departments)
            job_titles = JobTitle.objects.filter(department=department)
            job_title = random.choice(job_titles) if job_titles.exists() else None

            # Generate employee data
            employee_id = f"EMP{str(i+1).zfill(4)}"
            hire_date = date.today() - timedelta(days=random.randint(30, 1825))  # 1 month to 5 years ago
            
            # Location details
            building = random.choice(buildings)
            floor = random.choice(floors)
            desk_number = f"{random.randint(100, 999)}"
            
            # Phone numbers
            work_phone = f"{random.choice(phone_prefixes)}{random.randint(100, 999)}"
            mobile_phone = f"{random.choice(phone_prefixes)}{random.randint(100, 999)}"
            
            # Emergency contact
            emergency_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            emergency_phone = f"{random.choice(phone_prefixes)}{random.randint(100, 999)}"

            # Create employee record (independent from users)
            employee = Employee.objects.create(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=f"{username}@{random.choice(domains)}",
                department=department,
                job_title=job_title,
                hire_date=hire_date,
                employment_status='active',
                work_phone=work_phone,
                mobile_phone=mobile_phone,
                work_email=f"{username}@{random.choice(domains)}",
                office_location=f"{building}, {floor}",
                building=building,
                floor=floor.split()[1],  # Extract floor number
                desk_number=desk_number,
                cost_center=f"{department.code}-{random.randint(1000, 9999)}",
                emergency_contact_name=emergency_name,
                emergency_contact_phone=emergency_phone,
                notes=f"Mock employee data for {first_name} {last_name}"
            )

            # Optionally create system user for some employees (50% chance)
            if random.choice([True, False]):
                user = User.objects.create(
                    username=username,
                    email=employee.email,
                    first_name=first_name,
                    last_name=last_name,
                    password=make_password('password123'),
                    role='viewer',  # Most employees are viewers
                    is_active=True
                )
                employee.system_user = user
                employee.save()

            if i % 10 == 0:
                self.stdout.write(f'Created {i+1} employees...')

        self.stdout.write(f'Created {count} employees with mock data')