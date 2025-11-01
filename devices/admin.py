from django.contrib import admin
from .models import DeviceCategory, DeviceManufacturer, DeviceVendor, DeviceModel, Device, DeviceHistory
from .forms import DeviceModelForm, DeviceModelAdminForm, DeviceAdminForm


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


@admin.register(DeviceManufacturer)
class DeviceManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'support_contact', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'website', 'support_contact')
    readonly_fields = ('created_at',)


@admin.register(DeviceVendor)
class DeviceVendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'account_number', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_email', 'contact_phone', 'account_number')
    readonly_fields = ('created_at',)


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    form = DeviceModelForm
    list_display = ('manufacturer', 'model_name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'manufacturer', 'is_active', 'created_at')
    search_fields = ('manufacturer', 'model_name')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('manufacturer', 'model_name', 'category', 'is_active')
        }),
        ('Specifications', {
            'fields': ('spec_cpu', 'spec_ram', 'spec_storage', 'spec_gpu', 'spec_display', 'spec_os'),
            'description': 'CPU, RAM, and Storage are required. Other specifications are optional.'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    class Media:
        js = ('devices/admin/js/device_admin.js',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    form = DeviceAdminForm
    list_display = ('asset_tag', 'hostname', 'serial_number', 'device_model', 'status', 'assigned_to', 'usage_type', 'full_location')
    list_filter = ('status', 'usage_type', 'shared_usage', 'device_model__category', 'device_model__manufacturer', 'location', 'created_at')
    search_fields = ('asset_tag', 'hostname', 'serial_number', 'device_model__manufacturer', 'device_model__model_name', 'assigned_to__first_name', 'assigned_to__last_name', 'ip_address', 'mac_address')
    readonly_fields = ('created_at', 'updated_at', 'full_location')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_tag', 'hostname', 'serial_number', 'device_model', 'barcode')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Usage Information', {
            'fields': ('usage_type', 'shared_usage')
        }),
        ('Network Information', {
            'fields': ('ip_address', 'mac_address')
        }),
        ('Location', {
            'fields': ('location_choice', 'room', 'full_location')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    class Media:
        js = ('devices/admin/js/device_admin.js',)


@admin.register(DeviceHistory)
class DeviceHistoryAdmin(admin.ModelAdmin):
    list_display = ('device', 'action', 'previous_status', 'new_status', 'created_by', 'created_at')
    list_filter = ('action', 'previous_status', 'new_status', 'created_at')
    search_fields = ('device__asset_tag', 'notes')
    readonly_fields = ('device', 'action', 'previous_status', 'new_status', 'previous_employee', 'new_employee', 'notes', 'created_at', 'created_by')
    ordering = ('-created_at',)
