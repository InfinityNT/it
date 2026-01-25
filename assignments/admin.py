from django.contrib import admin
from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('device', 'employee', 'assigned_date', 'expected_return_date', 'status', 'assigned_by')
    list_filter = ('status', 'assigned_date', 'expected_return_date', 'device__device_model__category')
    search_fields = ('device__asset_tag', 'employee__employee_id', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('created_at', 'updated_at', 'days_assigned', 'is_overdue')
    date_hierarchy = 'assigned_date'
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('device', 'employee', 'assigned_by', 'assigned_date', 'expected_return_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('purpose', 'location', 'notes', 'return_notes')
        }),
        ('Approval', {
            'fields': ('requires_approval', 'approved_by', 'approved_date')
        }),
        ('Return Details', {
            'fields': ('actual_return_date',)
        }),
        ('Computed Fields', {
            'fields': ('days_assigned', 'is_overdue'),
            'classes': ('collapse',)
        })
    )