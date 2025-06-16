from django.contrib import admin
from .models import Assignment, MaintenanceRequest, DeviceReservation


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('device', 'user', 'assigned_date', 'expected_return_date', 'status', 'assigned_by')
    list_filter = ('status', 'assigned_date', 'expected_return_date', 'device__device_model__category')
    search_fields = ('device__asset_tag', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'days_assigned', 'is_overdue')
    date_hierarchy = 'assigned_date'
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('device', 'user', 'assigned_by', 'assigned_date', 'expected_return_date', 'status')
        }),
        ('Condition Tracking', {
            'fields': ('condition_at_assignment', 'condition_at_return')
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


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('device', 'title', 'priority', 'status', 'requested_by', 'assigned_to', 'requested_date')
    list_filter = ('status', 'priority', 'requested_date', 'device__device_model__category')
    search_fields = ('device__asset_tag', 'title', 'description', 'requested_by__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'requested_date'
    
    fieldsets = (
        ('Request Details', {
            'fields': ('device', 'title', 'description', 'priority', 'status', 'requested_by', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('requested_date', 'approved_date', 'started_date', 'completed_date')
        }),
        ('Cost Information', {
            'fields': ('estimated_cost', 'actual_cost', 'vendor')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'parts_replaced')
        })
    )


@admin.register(DeviceReservation)
class DeviceReservationAdmin(admin.ModelAdmin):
    list_display = ('device', 'user', 'start_date', 'end_date', 'status', 'purpose')
    list_filter = ('status', 'start_date', 'end_date', 'device__device_model__category')
    search_fields = ('device__asset_tag', 'user__username', 'user__first_name', 'user__last_name', 'purpose')
    readonly_fields = ('created_at', 'updated_at', 'is_expired')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Reservation Details', {
            'fields': ('device', 'user', 'start_date', 'end_date', 'purpose', 'status')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_date', 'rejection_reason')
        }),
        ('Fulfillment', {
            'fields': ('fulfilled_date', 'assignment')
        }),
        ('Computed Fields', {
            'fields': ('is_expired',),
            'classes': ('collapse',)
        })
    )
