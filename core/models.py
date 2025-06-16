from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Extended user model with additional fields for IT management"""
    ROLE_CHOICES = [
        ('superuser', 'IT Manager'),
        ('staff', 'IT Staff'),
        ('viewer', 'Viewer'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def is_superuser_role(self):
        """Check if user has superuser (IT Manager) role"""
        return self.role == 'superuser'
    
    @property
    def is_staff_role(self):
        """Check if user has staff (IT Staff) role"""
        return self.role == 'staff'
    
    @property
    def is_viewer_role(self):
        """Check if user has viewer role"""
        return self.role == 'viewer'
    
    @property
    def can_modify_devices(self):
        """Check if user can modify devices"""
        return self.role in ['superuser', 'staff']
    
    @property
    def can_assign_devices(self):
        """Check if user can assign/return devices"""
        return self.role in ['superuser', 'staff']
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['superuser', 'staff']
    
    @property
    def can_access_admin(self):
        """Check if user can access Django admin"""
        return self.role == 'superuser'
    
    @property
    def can_manage_system_settings(self):
        """Check if user can manage system settings"""
        return self.role == 'superuser'

    class Meta:
        db_table = 'core_user'


class AuditLog(models.Model):
    """Track all important actions in the system"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('assign', 'Assign'),
        ('unassign', 'Unassign'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50, null=True, blank=True)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} on {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class SystemSettings(models.Model):
    """System-wide settings and feature toggles"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name_plural = "System Settings"
