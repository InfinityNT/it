from django.contrib import admin
from .models import Department, JobTitle, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'location', 'created_at')
    search_fields = ('name', 'code', 'description', 'budget_code')
    readonly_fields = ('created_at',)


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'level', 'is_active', 'created_at')
    list_filter = ('department', 'level', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'job_title', 'employment_status', 'hire_date')
    list_filter = ('employment_status', 'department', 'job_title', 'hire_date', 'office_location')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'is_active_employee')
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'department', 'job_title', 'manager')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'termination_date', 'employment_status')
        }),
        ('Contact Information', {
            'fields': ('work_phone', 'mobile_phone', 'work_email')
        }),
        ('Location Information', {
            'fields': ('office_location', 'building', 'floor', 'desk_number')
        }),
        ('Additional Information', {
            'fields': ('cost_center', 'emergency_contact_name', 'emergency_contact_phone', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_active_employee'),
            'classes': ('collapse',)
        })
    )
