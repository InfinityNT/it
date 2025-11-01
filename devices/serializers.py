from rest_framework import serializers
from .models import DeviceCategory, DeviceManufacturer, DeviceVendor, DeviceModel, Device, DeviceHistory
from core.serializers import UserSerializer
from employees.models import Employee


class DeviceCategorySerializer(serializers.ModelSerializer):
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'device_count']
    
    def get_device_count(self, obj):
        return Device.objects.filter(device_model__category=obj).count()


class DeviceManufacturerSerializer(serializers.ModelSerializer):
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceManufacturer
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'device_count']
    
    def get_device_count(self, obj):
        return Device.objects.filter(device_model__manufacturer=obj.name).count()


class DeviceVendorSerializer(serializers.ModelSerializer):
    device_count = serializers.SerializerMethodField()

    class Meta:
        model = DeviceVendor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'device_count']

    def get_device_count(self, obj):
        # Vendor field removed from Device model
        return 0


class DeviceModelSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceModel
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'category_name', 'device_count']
    
    def get_device_count(self, obj):
        return obj.device_set.count()


class DeviceSerializer(serializers.ModelSerializer):
    device_model_display = serializers.CharField(source='device_model.__str__', read_only=True)
    category = serializers.CharField(source='device_model.category.name', read_only=True)
    assigned_to_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    usage_type_display = serializers.CharField(source='get_usage_type_display', read_only=True)
    shared_usage_display = serializers.CharField(source='get_shared_usage_display', read_only=True)
    full_location = serializers.ReadOnlyField()

    def get_assigned_to_display(self, obj):
        """Get display name for assigned employee"""
        if obj.assigned_to:
            return obj.assigned_to.get_full_name()
        return None

    class Meta:
        model = Device
        fields = [
            'id', 'asset_tag', 'hostname', 'serial_number', 'device_model', 'device_model_display',
            'category', 'status', 'status_display',
            'usage_type', 'usage_type_display', 'shared_usage', 'shared_usage_display',
            'ip_address', 'mac_address',
            'location', 'full_location',
            'assigned_to', 'assigned_to_display', 'assigned_date',
            'notes', 'barcode', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'device_model_display', 'category',
            'assigned_to_display', 'status_display',
            'usage_type_display', 'shared_usage_display', 'full_location'
        ]


class DeviceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'asset_tag', 'hostname', 'serial_number', 'device_model', 'status',
            'usage_type', 'shared_usage', 'ip_address', 'mac_address',
            'location',
            'notes', 'barcode'
        ]

    def create(self, validated_data):
        # Set created_by to current user
        if 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DeviceHistorySerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    previous_employee_display = serializers.CharField(source='previous_employee.get_full_name', read_only=True)
    new_employee_display = serializers.CharField(source='new_employee.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = DeviceHistory
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'device_display', 'created_by_display',
            'previous_employee_display', 'new_employee_display', 'action_display'
        ]


class DeviceAssignSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)  # Keep for backward compatibility
    notes = serializers.CharField(required=False, allow_blank=True)
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    
    def validate(self, attrs):
        employee_id = attrs.get('employee_id') or attrs.get('user_id')
        if not employee_id:
            raise serializers.ValidationError("Either employee_id or user_id is required")
        
        try:
            employee = Employee.objects.get(id=employee_id, employment_status='active')
            return attrs
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employee not found or not active")


class DeviceUnassignSerializer(serializers.Serializer):
    condition = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)