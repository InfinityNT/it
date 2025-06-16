from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from core.models import User


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
    manufacturer = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    specifications = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.manufacturer} {self.model_name}"

    class Meta:
        unique_together = ['manufacturer', 'model_name']
        ordering = ['manufacturer', 'model_name']
        verbose_name_plural = "Device Models"


class Device(models.Model):
    """Individual device instances"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost/Stolen'),
        ('damaged', 'Damaged'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    # Basic Information
    asset_tag = models.CharField(max_length=50, unique=True, 
                                validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Asset tag must contain only uppercase letters, numbers, and hyphens')])
    serial_number = models.CharField(max_length=100, unique=True)
    device_model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE)
    
    # Status and Condition
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    
    # Purchase Information
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=100, blank=True)
    
    # Location and Assignment
    location = models.CharField(max_length=100, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_devices')
    assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_devices')

    def __str__(self):
        return f"{self.asset_tag} - {self.device_model}"

    @property
    def is_under_warranty(self):
        if self.warranty_expiry:
            return self.warranty_expiry > timezone.now().date()
        return False

    def save(self, *args, **kwargs):
        # Set assigned_date when device is assigned
        if self.assigned_to and not self.assigned_date:
            self.assigned_date = timezone.now()
        elif not self.assigned_to:
            self.assigned_date = None
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
            models.Index(fields=['location']),
            
            # Date-based queries
            models.Index(fields=['assigned_date']),
            models.Index(fields=['purchase_date']),
            models.Index(fields=['warranty_expiry']),
        ]


class DeviceHistory(models.Model):
    """Track device status changes and assignments"""
    ACTION_CHOICES = [
        ('created', 'Device Created'),
        ('assigned', 'Assigned to User'),
        ('unassigned', 'Unassigned from User'),
        ('status_change', 'Status Changed'),
        ('maintenance', 'Sent for Maintenance'),
        ('returned', 'Returned from Maintenance'),
        ('retired', 'Retired'),
        ('updated', 'Updated'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    previous_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_assignments')
    new_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='new_assignments')
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
            
            # User assignment tracking  
            models.Index(fields=['new_user', '-created_at']),
            models.Index(fields=['previous_user', '-created_at']),
        ]
