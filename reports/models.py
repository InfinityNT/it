from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ReportTemplate(models.Model):
    """Predefined report templates"""
    REPORT_TYPES = [
        ('inventory', 'Device Inventory Report'),
        ('assignments', 'Assignment History Report'),
        ('utilization', 'Utilization Analysis'),
        ('maintenance', 'Maintenance Report'),
        ('cost', 'Cost Analysis Report'),
        ('user_activity', 'User Activity Report'),
        ('custom', 'Custom Report'),
    ]
    
    OUTPUT_FORMATS = [
        ('csv', 'CSV (Excel Compatible)'),
        ('pdf', 'PDF Report'),
        ('json', 'JSON Data'),
        ('xlsx', 'Excel Spreadsheet'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    default_format = models.CharField(max_length=10, choices=OUTPUT_FORMATS, default='csv')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ReportGeneration(models.Model):
    """Track report generation history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=20)
    format = models.CharField(max_length=10)
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    record_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.generated_by.username} - {self.requested_at}"
    
    def mark_completed(self, file_path=None, record_count=None, file_size=None):
        """Mark report as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if file_path:
            self.file_path = file_path
        if record_count is not None:
            self.record_count = record_count
        if file_size is not None:
            self.file_size = file_size
        self.save()
    
    def mark_failed(self, error_message):
        """Mark report as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
