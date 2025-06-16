from django.db import models
from django.utils import timezone
from core.models import User
from devices.models import Device


class Assignment(models.Model):
    """Device assignments to users"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('pending_return', 'Pending Return'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_devices_by')
    
    # Assignment Details
    assigned_date = models.DateTimeField(default=timezone.now)
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Condition tracking
    condition_at_assignment = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    condition_at_return = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    
    # Additional Information
    purpose = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    return_notes = models.TextField(blank=True)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_assignments')
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_request = models.ForeignKey('approvals.ApprovalRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_assignments')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.device.asset_tag} → {self.user.get_full_name()}"

    @property
    def is_overdue(self):
        if self.expected_return_date and self.status == 'active':
            return self.expected_return_date < timezone.now().date()
        return False

    @property
    def days_assigned(self):
        if self.status == 'active':
            return (timezone.now().date() - self.assigned_date.date()).days
        elif self.actual_return_date:
            return (self.actual_return_date.date() - self.assigned_date.date()).days
        return 0

    def return_device(self, returned_by, condition=None, notes=None):
        """Handle device return process"""
        self.actual_return_date = timezone.now()
        self.status = 'returned'
        if condition:
            self.condition_at_return = condition
        if notes:
            self.return_notes = notes
        self.save()

        # Update device status
        self.device.status = 'available'
        self.device.assigned_to = None
        self.device.assigned_date = None
        if condition:
            self.device.condition = condition
        self.device.save()

    class Meta:
        ordering = ['-assigned_date']
        indexes = [
            # Primary query patterns
            models.Index(fields=['device', 'status']),  # Device assignment status
            models.Index(fields=['user', '-assigned_date']),  # User assignment history
            models.Index(fields=['status', '-assigned_date']),  # Status-based queries
            models.Index(fields=['assigned_by', '-assigned_date']),  # Who assigned what
            
            # Active assignment queries (most common)
            models.Index(fields=['device', 'status', 'user']),  # Find active assignment for device
            models.Index(fields=['user', 'status']),  # User's active assignments
            
            # Date-based queries
            models.Index(fields=['assigned_date']),
            models.Index(fields=['expected_return_date']),
            models.Index(fields=['actual_return_date']),
            
            # Overdue assignment detection
            models.Index(fields=['status', 'expected_return_date']),
            
            # Condition tracking
            models.Index(fields=['condition_at_assignment']),
            models.Index(fields=['condition_at_return']),
            
            # Statistics and reporting
            models.Index(fields=['status', 'actual_return_date']),  # Returned this month
            models.Index(fields=['created_at']),  # Assignment creation tracking
        ]


class MaintenanceRequest(models.Model):
    """Track maintenance requests for devices"""
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='maintenance_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance')
    
    # Request Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    
    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    started_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Cost and Vendor
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vendor = models.CharField(max_length=100, blank=True)
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    parts_replaced = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.device.asset_tag} - {self.title}"

    class Meta:
        ordering = ['-requested_date']


class DeviceReservation(models.Model):
    """Allow users to reserve available devices"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_reservations')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reservations')
    
    # Reservation Details
    start_date = models.DateField()
    end_date = models.DateField()
    purpose = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Fulfillment
    fulfilled_date = models.DateTimeField(null=True, blank=True)
    assignment = models.OneToOneField(Assignment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.device.asset_tag} ({self.start_date} to {self.end_date})"

    @property
    def is_expired(self):
        return self.start_date < timezone.now().date() and self.status == 'pending'

    class Meta:
        ordering = ['-created_at']
