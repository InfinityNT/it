from django.db import models
from core.models import User


class Department(models.Model):
    """Organization departments"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    manager_employee_id = models.CharField(max_length=50, blank=True, help_text="Manager's employee ID")
    budget_code = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def manager(self):
        """Get department manager as Employee object"""
        if self.manager_employee_id:
            try:
                return Employee.objects.get(employee_id=self.manager_employee_id)
            except Employee.DoesNotExist:
                return None
        return None

    class Meta:
        ordering = ['name']


class JobTitle(models.Model):
    """Job titles within the organization"""
    title = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    level = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.department.name}"

    class Meta:
        verbose_name_plural = "Job Titles"
        ordering = ['title']


class Employee(models.Model):
    """HR employee records - independent from system users"""
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]

    # Basic Information
    employee_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    
    # Optional link to system user (if they have portal access)
    system_user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='employee_profile',
        help_text="Link to system user account if employee has portal access"
    )
    
    # Organizational Information
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    job_title = models.ForeignKey(JobTitle, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="Employee position/title in the organization")
    manager_employee_id = models.CharField(max_length=50, blank=True, help_text="Manager's employee ID")

    # Employment Details
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    
    # Contact Information
    work_phone = models.CharField(max_length=20, blank=True)
    mobile_phone = models.CharField(max_length=20, blank=True)
    work_email = models.EmailField(blank=True, help_text="Different from personal email if needed")
    
    # Location Information
    office_location = models.CharField(max_length=100, blank=True)
    desk_number = models.CharField(max_length=20, blank=True, help_text="Desk/cubicle number within the location")
    
    # Department Responsibility
    is_department_responsible = models.BooleanField(
        default=False,
        help_text="Designate this employee as the responsible person for their department"
    )

    # Additional Information
    cost_center = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active_employee(self):
        return self.employment_status == 'active'
    
    @property
    def has_system_access(self):
        """Check if employee has system user account"""
        return self.system_user is not None and self.system_user.is_active
    
    @property
    def manager(self):
        """Get manager as Employee object"""
        if self.manager_employee_id:
            try:
                return Employee.objects.get(employee_id=self.manager_employee_id)
            except Employee.DoesNotExist:
                return None
        return None

    class Meta:
        ordering = ['employee_id']
