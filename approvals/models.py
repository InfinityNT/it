from django.db import models
from django.utils import timezone
from core.models import User
from devices.models import Device


class ApprovalRequest(models.Model):
    """Model for approval requests in the system"""
    
    REQUEST_TYPES = [
        ('device_assignment', 'Device Assignment'),
        ('device_return', 'Device Return'),
        ('device_transfer', 'Device Transfer'),
        ('bulk_operation', 'Bulk Operation'),
        ('extended_assignment', 'Extended Assignment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic request information
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Request details (stored as JSON for flexibility)
    request_data = models.JSONField(default=dict, help_text="Serialized request details")
    
    # Users involved
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_approvals')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this request expires if not processed")
    
    # Additional information
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Related objects
    devices = models.ManyToManyField(Device, blank=True, related_name='approval_requests')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.title}"
    
    def approve(self, approved_by, notes=''):
        """Approve the request"""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approval_notes = notes
        self.reviewed_at = timezone.now()
        self.save()
        
        # Execute the approved action
        self._execute_approved_action()
        
        # Create notification
        self._create_notification('approved')
    
    def reject(self, rejected_by, reason=''):
        """Reject the request"""
        self.status = 'rejected'
        self.approved_by = rejected_by
        self.rejection_reason = reason
        self.reviewed_at = timezone.now()
        self.save()
        
        # Create notification
        self._create_notification('rejected')

    def _execute_approved_action(self):
        """Execute the action that was approved"""
        if self.request_type == 'device_assignment':
            self._execute_device_assignment()
        elif self.request_type == 'device_return':
            self._execute_device_return()
        elif self.request_type == 'bulk_operation':
            self._execute_bulk_operation()
        # Add more execution logic as needed
    
    def _execute_device_assignment(self):
        """Execute a device assignment"""
        try:
            from assignments.models import Assignment
            from employees.models import Employee
            data = self.request_data
            
            device = Device.objects.get(id=data['device_id'])
            employee = Employee.objects.get(id=data['employee_id'])
            
            # Update device
            device.assigned_to = employee
            device.status = 'assigned'
            device.save()
            
            # Create assignment record
            Assignment.objects.create(
                device=device,
                employee=employee,
                assigned_by=self.approved_by or self.requested_by,
                expected_return_date=data.get('expected_return_date'),
                notes=f"Approved assignment - {self.approval_notes}",
                condition_at_assignment=device.condition,
                approval_request=self
            )
            
            # Create history record
            from devices.models import DeviceHistory
            DeviceHistory.objects.create(
                device=device,
                action='assigned',
                new_employee=employee,
                new_status='assigned',
                previous_status='available',
                notes=f'Assignment approved via request #{self.id}',
                created_by=self.approved_by or self.requested_by
            )
            
        except Exception as e:
            # Log error and update request
            self.approval_notes += f"\nExecution error: {str(e)}"
            self.save()
    
    def _execute_device_return(self):
        """Execute a device return"""
        try:
            from assignments.models import Assignment
            data = self.request_data
            
            # Get the assignment
            assignment = Assignment.objects.get(id=data['assignment_id'])
            device = assignment.device
            
            # Return the device
            assignment.return_device(
                returned_by=self.approved_by or self.requested_by,
                condition=data.get('condition_at_return', device.condition),
                notes=data.get('comprehensive_notes', f"Return approved via request #{self.id}")
            )
            
            # Update device status based on next action if specified
            next_action = data.get('next_action')
            if next_action == 'retired':
                device.status = 'retired'
            else:
                device.status = 'available'
            device.save()
            
            # Create history record
            from devices.models import DeviceHistory
            DeviceHistory.objects.create(
                device=device,
                action='returned',
                previous_employee=assignment.employee,
                previous_status='assigned',
                new_status=device.status,
                notes=f'Return approved via request #{self.id}',
                created_by=self.approved_by or self.requested_by
            )
            
        except Exception as e:
            # Log error and update request
            self.approval_notes += f"\nExecution error: {str(e)}"
            self.save()
    
    def _execute_bulk_operation(self):
        """Execute a bulk operation"""
        try:
            # Implementation for bulk operations
            # This would call the existing bulk operations view logic
            pass
        except Exception as e:
            self.approval_notes += f"\nExecution error: {str(e)}"
            self.save()
    
    def _create_notification(self, action):
        """Create notification for request status change"""
        # This will be implemented when we add the notification system
        pass
    
    @property
    def is_expired(self):
        """Check if the request has expired"""
        if self.expires_at and self.status == 'pending':
            return timezone.now() > self.expires_at
        return False
    
    @property
    def days_pending(self):
        """Calculate how many days the request has been pending"""
        if self.status == 'pending':
            return (timezone.now() - self.created_at).days
        return 0


class ApprovalComment(models.Model):
    """Comments on approval requests"""
    
    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user} on {self.request}"