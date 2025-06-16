from rest_framework import serializers
from .models import DeviceCategory, DeviceModel, Device, DeviceHistory
from core.serializers import UserSerializer


class DeviceCategorySerializer(serializers.ModelSerializer):
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'device_count']
    
    def get_device_count(self, obj):
        return Device.objects.filter(device_model__category=obj).count()


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
    assigned_to_display = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    is_under_warranty = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'asset_tag', 'serial_number', 'device_model', 'device_model_display',
            'category', 'status', 'status_display', 'condition', 'condition_display',
            'purchase_date', 'purchase_price', 'warranty_expiry', 'vendor',
            'location', 'assigned_to', 'assigned_to_display', 'assigned_date',
            'notes', 'barcode', 'is_under_warranty', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'device_model_display', 'category',
            'assigned_to_display', 'is_under_warranty', 'status_display', 'condition_display'
        ]


class DeviceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'asset_tag', 'serial_number', 'device_model', 'status', 'condition',
            'purchase_date', 'purchase_price', 'warranty_expiry', 'vendor',
            'location', 'notes', 'barcode'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DeviceHistorySerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    created_by_display = serializers.CharField(source='created_by.get_full_name', read_only=True)
    previous_user_display = serializers.CharField(source='previous_user.get_full_name', read_only=True)
    new_user_display = serializers.CharField(source='new_user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = DeviceHistory
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'device_display', 'created_by_display',
            'previous_user_display', 'new_user_display', 'action_display'
        ]


class DeviceAssignSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    
    def validate_user_id(self, value):
        from core.models import User
        try:
            user = User.objects.get(id=value, is_active_employee=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found or not an active employee")


class DeviceUnassignSerializer(serializers.Serializer):
    condition = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)