from django.db import models
from django.utils import timezone
from core.models import User
from devices.models import Device
from employees.models import Employee


class Assignment(models.Model):
    """Device assignments to users"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('pending_return', 'Pending Return'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='device_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_devices_by')

    # Assignment Details
    assigned_date = models.DateTimeField(default=timezone.now)
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

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
        return f"{self.device.asset_tag} → {self.employee.get_full_name()}"

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

    def return_device(self, returned_by, notes=None):
        """Handle device return process"""
        self.actual_return_date = timezone.now()
        self.status = 'returned'
        if notes:
            self.return_notes = notes
        self.save()

        # Update device status
        self.device.status = 'available'
        self.device.assigned_to = None
        self.device.assigned_date = None
        self.device.save()

    class Meta:
        ordering = ['-assigned_date']
        indexes = [
            # Primary query patterns
            models.Index(fields=['device', 'status']),  # Device assignment status
            models.Index(fields=['employee', '-assigned_date']),  # Employee assignment history
            models.Index(fields=['status', '-assigned_date']),  # Status-based queries
            models.Index(fields=['assigned_by', '-assigned_date']),  # Who assigned what
            
            # Active assignment queries (most common)
            models.Index(fields=['device', 'status', 'employee']),  # Find active assignment for device
            models.Index(fields=['employee', 'status']),  # Employee's active assignments
            
            # Date-based queries
            models.Index(fields=['assigned_date']),
            models.Index(fields=['expected_return_date']),
            models.Index(fields=['actual_return_date']),
            
            # Overdue assignment detection
            models.Index(fields=['status', 'expected_return_date']),

            # Statistics and reporting
            models.Index(fields=['status', 'actual_return_date']),  # Returned this month
            models.Index(fields=['created_at']),  # Assignment creation tracking
        ]



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
