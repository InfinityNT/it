from django.db import models
from django.core.validators import RegexValidator, ValidationError
from django.utils import timezone
from core.models import User
from employees.models import Employee


class DeviceManufacturer(models.Model):
    """Device manufacturers like Apple, Dell, HP, etc."""
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True, help_text="Manufacturer's website")
    support_contact = models.CharField(max_length=200, blank=True, help_text="Support contact information")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Device Manufacturers"


class DeviceVendor(models.Model):
    """Device vendors/suppliers like Amazon, Best Buy, CDW, etc."""
    name = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    account_number = models.CharField(max_length=50, blank=True, help_text="Account number with vendor")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Device Vendors"


class DeviceCategory(models.Model):
    """Device categories like Laptop, Desktop, Phone, etc."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Device Categories"
        ordering = ['name']


class DeviceModel(models.Model):
    """Specific device models like MacBook Pro 2023, Dell Latitude 7420, etc."""
    category = models.ForeignKey(DeviceCategory, on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=100)  # Using CharField for compatibility
    model_name = models.CharField(max_length=100)
    specifications = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.manufacturer} {self.model_name}"
    
    def get_manufacturer_obj(self):
        """Get the DeviceManufacturer object for this model"""
        try:
            return DeviceManufacturer.objects.get(name=self.manufacturer)
        except DeviceManufacturer.DoesNotExist:
            return None

    class Meta:
        unique_together = ['manufacturer', 'model_name']
        ordering = ['manufacturer', 'model_name']
        verbose_name_plural = "Device Models"


class Device(models.Model):
    """Individual device instances"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('retired', 'Retired'),
        ('lost', 'Lost/Stolen'),
        ('damaged', 'Damaged'),
    ]

    USAGE_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('shared', 'Shared'),
    ]

    SHARED_USAGE_CHOICES = [
        ('kiosk', 'Kiosk'),
        ('training', 'Training'),
        ('shared', 'Shared'),
    ]

    # Basic Information - Three unique identifiers
    asset_tag = models.CharField(max_length=50, unique=True,
                                validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Asset tag must contain only uppercase letters, numbers, and hyphens')],
                                help_text="Organization's main asset tracking number")
    serial_number = models.CharField(max_length=100, unique=True, help_text="Manufacturer's serial number")
    device_model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    # Network Information
    ip_address = models.GenericIPAddressField(null=True, blank=True, unique=True, help_text="IPv4 or IPv6 address")
    mac_address = models.CharField(max_length=17, blank=True, unique=True, null=True,
                                  validators=[RegexValidator(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', 
                                                           'MAC address must be in format XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX')],
                                  help_text="MAC address in format XX:XX:XX:XX:XX:XX")
    
    # Usage Information
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPE_CHOICES, default='individual')
    shared_usage = models.CharField(max_length=20, choices=SHARED_USAGE_CHOICES, blank=True, null=True,
                                   help_text="Required if usage_type is 'shared'")
    
    # Assignment - Changed to use Employee model instead of User
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_devices')
    assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    hostname = models.CharField(max_length=100, blank=True, unique=True, null=True,
                               help_text="Device hostname (default: MEX-[last 6 of serial])")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_devices')

    def __str__(self):
        return f"{self.asset_tag} - {self.device_model}"

    def clean(self):
        """Validate model data"""
        # Validate shared usage
        if self.usage_type == 'shared' and not self.shared_usage:
            raise ValidationError({'shared_usage': 'Shared usage type is required when usage type is "shared"'})
        
        if self.usage_type == 'individual' and self.shared_usage:
            raise ValidationError({'shared_usage': 'Shared usage type should be empty when usage type is "individual"'})

        # Validate MAC address format (normalize to uppercase with colons)
        if self.mac_address:
            mac = self.mac_address.replace('-', ':').upper()
            self.mac_address = mac

    def save(self, *args, **kwargs):
        # Set assigned_date when device is assigned
        if self.assigned_to and not self.assigned_date:
            self.assigned_date = timezone.now()
        elif not self.assigned_to:
            self.assigned_date = None
        
        # Run validation
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['asset_tag']
        indexes = [
            # Most commonly queried fields
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['device_model']),
            models.Index(fields=['created_at']),
            
            # Composite indexes for common query patterns
            models.Index(fields=['status', 'assigned_to']),
            models.Index(fields=['status', 'device_model']),
            models.Index(fields=['device_model', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            
            # Search optimization indexes
            models.Index(fields=['asset_tag']),  # Already unique, but explicit index
            models.Index(fields=['serial_number']),
            models.Index(fields=['hostname']),
            
            # Network-related indexes
            models.Index(fields=['ip_address']),
            models.Index(fields=['mac_address']),
            
            # Usage-related indexes
            models.Index(fields=['usage_type']),
            models.Index(fields=['shared_usage']),
            models.Index(fields=['usage_type', 'shared_usage']),

            # Date-based queries
            models.Index(fields=['assigned_date']),
        ]


class DeviceHistory(models.Model):
    """Track device status changes and assignments"""
    ACTION_CHOICES = [
        ('created', 'Device Created'),
        ('assigned', 'Assigned to User'),
        ('unassigned', 'Unassigned from User'),
        ('status_change', 'Status Changed'),
        ('retired', 'Retired'),
        ('updated', 'Updated'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    previous_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_device_assignments')
    new_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='new_device_assignments')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='device_history_entries')

    def __str__(self):
        return f"{self.device.asset_tag} - {self.action} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Device Histories"
        indexes = [
            # Primary query patterns
            models.Index(fields=['device', '-created_at']),  # Device history chronological
            models.Index(fields=['action', '-created_at']),  # Action-based queries
            models.Index(fields=['created_by', '-created_at']),  # User activity tracking
            
            # Composite indexes for filtering
            models.Index(fields=['device', 'action']),
            models.Index(fields=['device', 'action', '-created_at']),
            
            # Status change tracking
            models.Index(fields=['previous_status', 'new_status']),
            models.Index(fields=['new_status', '-created_at']),
            
            # Employee assignment tracking  
            models.Index(fields=['new_employee', '-created_at']),
            models.Index(fields=['previous_employee', '-created_at']),
        ]
