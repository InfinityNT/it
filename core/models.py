from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Extended user model with additional fields for IT management"""
    
    # Optional link to employee record for users who represent specific employees
    linked_employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to employee record if this user represents a specific employee"
    )
    
    # Password management
    password_change_required = models.BooleanField(
        default=False,
        help_text="Force user to change password on next login"
    )
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user last changed their password"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def needs_password_change(self):
        """Check if user needs to change their password"""
        return self.password_change_required
    
    def set_password(self, raw_password):
        """Override to track password change time"""
        super().set_password(raw_password)
        self.password_changed_at = timezone.now()
        self.password_change_required = False
    
    @property
    def can_modify_devices(self):
        """Check if user can modify devices"""
        return self.has_perm('devices.can_modify_devices')
    
    @property
    def can_assign_devices(self):
        """Check if user can assign/return devices"""
        return self.has_perm('devices.can_assign_devices')
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.has_perm('core.can_modify_users')
    
    @property
    def can_access_admin(self):
        """Check if user can access Django admin"""
        return self.has_perm('core.can_access_admin')
    
    @property
    def can_manage_system_settings(self):
        """Check if user can manage system settings"""
        return self.has_perm('core.can_manage_system')
    
    @property 
    def can_view_devices(self):
        """Check if user can view devices"""
        return self.has_perm('devices.can_view_devices')
    
    @property
    def can_view_employees(self):
        """Check if user can view employees"""
        return self.has_perm('employees.can_view_employees')
    
    @property
    def can_modify_employees(self):
        """Check if user can modify employees"""
        return self.has_perm('employees.can_modify_employees')
    
    @property
    def can_view_assignments(self):
        """Check if user can view assignments"""
        return self.has_perm('assignments.can_view_assignments')
    
    @property
    def can_modify_assignments(self):
        """Check if user can modify assignments"""
        return self.has_perm('assignments.can_modify_assignments')
    
    @property
    def can_view_reports(self):
        """Check if user can view reports"""
        return self.has_perm('core.can_view_reports')
    
    @property
    def can_generate_reports(self):
        """Check if user can generate reports"""
        return self.has_perm('core.can_generate_reports')
    
    def get_enabled_quick_actions(self):
        """Get user's enabled quick actions that they have permission to use"""
        user_actions = self.quick_actions.filter(is_enabled=True).order_by('display_order', 'action_code')
        enabled_actions = []
        
        for action in user_actions:
            config = action.action_config
            # Check if user has permission for this action
            if config.get('permission') and not self.has_perm(config['permission']):
                continue
            
            enabled_actions.append({
                'code': action.action_code,
                'display_name': action.get_action_code_display(),
                'url': config.get('url'),
                'url_params': config.get('url_params', ''),
                'icon': config.get('icon', 'bi-circle'),
                'order': action.display_order
            })
        
        return enabled_actions
    
    def get_available_quick_actions(self):
        """Get all quick actions available to this user based on their permissions"""
        from core.models import UserQuickAction
        
        available_actions = []
        for code, display_name in UserQuickAction.AVAILABLE_ACTIONS:
            action = UserQuickAction(action_code=code)
            config = action.action_config
            
            # Check if user has permission for this action
            if config.get('permission') and not self.has_perm(config['permission']):
                continue
                
            # Check if user already has this action configured
            has_action = self.quick_actions.filter(action_code=code).exists()
            
            available_actions.append({
                'code': code,
                'display_name': display_name,
                'icon': config.get('icon', 'bi-circle'),
                'is_configured': has_action,
                'is_enabled': self.quick_actions.filter(action_code=code, is_enabled=True).exists() if has_action else False
            })
        
        return available_actions

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
    
    @classmethod
    def create_entry(cls, request, action, target_object, changes=None, notes=None):
        """Helper method to create consistent audit log entries"""
        return cls.objects.create(
            user=getattr(request, 'user', None) if hasattr(request, 'user') else None,
            action=action,
            model_name=target_object._meta.model_name.title(),
            object_id=str(target_object.pk) if target_object.pk else None,
            object_repr=str(target_object),
            changes=changes or {},
            ip_address=request.META.get('REMOTE_ADDR') if hasattr(request, 'META') else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if hasattr(request, 'META') else ''
        )


class UserQuickAction(models.Model):
    """User's personalized quick actions configuration"""
    AVAILABLE_ACTIONS = [
        ('add_device', 'Add Device'),
        ('assign_device', 'Assign Device'),
        ('return_device', 'Return Device'),
        ('quick_search', 'Quick Search'),
        ('add_user', 'Add User'),
        ('add_employee', 'Add Employee'),
        ('generate_report', 'Generate Report'),
        ('approvals', 'View Approvals'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quick_actions')
    action_code = models.CharField(max_length=50, choices=AVAILABLE_ACTIONS)
    display_order = models.PositiveIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'action_code']
        ordering = ['display_order', 'action_code']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_code_display()}"
    
    @property
    def action_config(self):
        """Get the configuration for this action including URL, icon, and permission requirements"""
        config = {
            'add_device': {
                'url': 'add-device',
                'icon': 'bi-plus-circle',
                'permission': 'devices.can_modify_devices',
            },
            'assign_device': {
                'url': 'assign-device',
                'icon': 'bi-person-plus',
                'permission': 'devices.can_assign_devices',
            },
            'return_device': {
                'url': 'return-device-page',
                'icon': 'bi-arrow-return-left',
                'permission': 'devices.can_assign_devices',
            },
            'quick_search': {
                'url': 'advanced-search',
                'icon': 'bi-search',
                'permission': None,  # Available to all authenticated users
            },
            'add_user': {
                'url': 'add-user-modal',
                'icon': 'bi-person-plus-fill',
                'permission': 'core.can_modify_users',
            },
            'add_employee': {
                'url': 'add-employee',
                'icon': 'bi-person-badge',
                'permission': 'employees.can_modify_employees',
            },
            'generate_report': {
                'url': 'reports:custom-report-form',
                'icon': 'bi-file-earmark-text',
                'permission': 'core.can_view_reports',
            },
            'approvals': {
                'url': 'approvals',
                'icon': 'bi-check-circle',
                'permission': 'assignments.can_modify_assignments',
            },
        }
        return config.get(self.action_code, {})


class Location(models.Model):
    """Predefined locations for devices, employees and reports"""
    name = models.CharField(max_length=100, unique=True, help_text="Location name (e.g., 'Main Office', 'Remote', 'Building A - Floor 2')")
    code = models.CharField(max_length=20, unique=True, help_text="Short code for location (e.g., 'MAIN', 'REMOTE', 'BA-F2')")
    description = models.TextField(blank=True, help_text="Additional details about this location")
    address = models.TextField(blank=True, help_text="Physical address if applicable")
    building = models.CharField(max_length=50, blank=True, help_text="Building identifier")
    floor = models.CharField(max_length=10, blank=True, help_text="Floor number/identifier")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Locations"


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
