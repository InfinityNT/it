from django.contrib import admin
from .models import DeviceCategory, DeviceModel, Device, DeviceHistory


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'model_name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'manufacturer', 'is_active', 'created_at')
    search_fields = ('manufacturer', 'model_name')
    readonly_fields = ('created_at',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('asset_tag', 'serial_number', 'device_model', 'status', 'condition', 'assigned_to', 'location')
    list_filter = ('status', 'condition', 'device_model__category', 'device_model__manufacturer', 'location', 'created_at')
    search_fields = ('asset_tag', 'serial_number', 'device_model__manufacturer', 'device_model__model_name', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'is_under_warranty')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_tag', 'serial_number', 'device_model', 'barcode')
        }),
        ('Status', {
            'fields': ('status', 'condition')
        }),
        ('Purchase Information', {
            'fields': ('purchase_date', 'purchase_price', 'warranty_expiry', 'vendor')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_date', 'location')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_under_warranty'),
            'classes': ('collapse',)
        })
    )


@admin.register(DeviceHistory)
class DeviceHistoryAdmin(admin.ModelAdmin):
    list_display = ('device', 'action', 'previous_status', 'new_status', 'created_by', 'created_at')
    list_filter = ('action', 'previous_status', 'new_status', 'created_at')
    search_fields = ('device__asset_tag', 'notes')
    readonly_fields = ('device', 'action', 'previous_status', 'new_status', 'previous_user', 'new_user', 'notes', 'created_at', 'created_by')
    ordering = ('-created_at',)
