from django.db import models
from django.utils import timezone
from core.models import User
from devices.models import Device


class ApprovalRequest(models.Model):
    """Model for approval requests in the system"""
    
    REQUEST_TYPES = [
        ('device_assignment', 'Device Assignment'),
        ('device_transfer', 'Device Transfer'),
        ('bulk_operation', 'Bulk Operation'),
        ('high_value_assignment', 'High Value Assignment'),
        ('extended_assignment', 'Extended Assignment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto Approved'),
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
    
    def auto_approve(self):
        """Auto-approve the request based on rules"""
        self.status = 'auto_approved'
        self.reviewed_at = timezone.now()
        self.approval_notes = 'Auto-approved by system'
        self.save()
        
        # Execute the approved action
        self._execute_approved_action()
        
        # Create notification
        self._create_notification('auto_approved')
    
    def _execute_approved_action(self):
        """Execute the action that was approved"""
        if self.request_type == 'device_assignment':
            self._execute_device_assignment()
        elif self.request_type == 'bulk_operation':
            self._execute_bulk_operation()
        # Add more execution logic as needed
    
    def _execute_device_assignment(self):
        """Execute a device assignment"""
        try:
            from assignments.models import Assignment
            data = self.request_data
            
            device = Device.objects.get(id=data['device_id'])
            user = User.objects.get(id=data['user_id'])
            
            # Update device
            device.assigned_to = user
            device.status = 'assigned'
            device.save()
            
            # Create assignment record
            Assignment.objects.create(
                device=device,
                user=user,
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
                new_user=user,
                new_status='assigned',
                previous_status='available',
                notes=f'Assignment approved via request #{self.id}',
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


class ApprovalRule(models.Model):
    """Rules for automatic approval or assignment"""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Rule conditions (stored as JSON)
    conditions = models.JSONField(default=dict, help_text="Conditions that trigger this rule")
    
    # Rule actions
    auto_approve = models.BooleanField(default=False)
    assign_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    priority_override = models.CharField(max_length=10, choices=ApprovalRequest.PRIORITY_CHOICES, blank=True)
    
    # Rule settings
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Order of rule evaluation")
    
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_approval_rules')
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def matches_request(self, request):
        """Check if this rule matches the given approval request"""
        conditions = self.conditions
        
        # Check request type
        if 'request_types' in conditions:
            if request.request_type not in conditions['request_types']:
                return False
        
        # Check device value (for high-value assignments)
        if 'max_device_value' in conditions:
            device_value = request.request_data.get('device_value', 0)
            if device_value > conditions['max_device_value']:
                return False
        
        # Check user role
        if 'requester_roles' in conditions:
            if request.requested_by.role not in conditions['requester_roles']:
                return False
        
        # Check assignment duration
        if 'max_assignment_days' in conditions:
            assignment_days = request.request_data.get('assignment_days', 0)
            if assignment_days > conditions['max_assignment_days']:
                return False
        
        return True


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