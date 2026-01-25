from django.contrib import admin
from .models import Department, JobTitle, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager_employee_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'budget_code', 'manager_employee_id')
    readonly_fields = ('created_at',)


@admin.register(JobTitle)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'level', 'is_active', 'created_at')
    list_filter = ('department', 'level', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'email', 'department', 'job_title', 'employment_status', 'has_system_access', 'hire_date')
    list_filter = ('employment_status', 'department', 'job_title', 'hire_date', 'office_location')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email', 'work_email')
    readonly_fields = ('created_at', 'updated_at', 'is_active_employee', 'has_system_access')
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'system_user')
        }),
        ('Organizational Information', {
            'fields': ('department', 'job_title', 'position', 'manager_employee_id')
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
            'fields': ('created_at', 'updated_at', 'is_active_employee', 'has_system_access'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def has_system_access(self, obj):
        return obj.has_system_access
    has_system_access.boolean = True
    has_system_access.short_description = 'System Access'
