from rest_framework import serializers
from .models import Assignment, MaintenanceRequest, DeviceReservation
from devices.serializers import DeviceSerializer
from core.serializers import UserSerializer


class AssignmentSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    user_display = serializers.CharField(source='user.get_full_name', read_only=True)
    assigned_by_display = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_assigned = serializers.ReadOnlyField()
    
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'device_display', 'user_display',
            'assigned_by_display', 'status_display', 'is_overdue', 'days_assigned'
        ]


class AssignmentListSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    user_display = serializers.CharField(source='user.get_full_name', read_only=True)
    assigned_by_display = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    device = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'device', 'user', 'assigned_date', 'expected_return_date', 
            'actual_return_date', 'status', 'condition_at_assignment', 'condition_at_return',
            'device_display', 'user_display', 'assigned_by_display', 'status_display', 'is_overdue'
        ]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            'device', 'user', 'expected_return_date', 'condition_at_assignment',
            'purpose', 'location', 'notes', 'requires_approval'
        ]
    
    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    requested_by_display = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    assigned_to_display = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'requested_date', 'device_display',
            'requested_by_display', 'assigned_to_display', 'status_display', 'priority_display'
        ]


class MaintenanceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = [
            'device', 'title', 'description', 'priority', 'estimated_cost'
        ]
    
    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


class DeviceReservationSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    user_display = serializers.CharField(source='user.get_full_name', read_only=True)
    approved_by_display = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = DeviceReservation
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'device_display', 'user_display',
            'approved_by_display', 'status_display', 'is_expired'
        ]


class DeviceReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceReservation
        fields = ['device', 'start_date', 'end_date', 'purpose']
    
    def validate(self, attrs):
        if attrs['start_date'] >= attrs['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReservationApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting")
        return attrs