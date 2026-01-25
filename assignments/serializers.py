from rest_framework import serializers
from .models import Assignment
from devices.serializers import DeviceSerializer
from core.serializers import UserSerializer


class AssignmentSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    employee_display = serializers.CharField(source='employee.get_full_name', read_only=True)
    assigned_by_display = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_assigned = serializers.ReadOnlyField()
    
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'device_display', 'employee_display',
            'assigned_by_display', 'status_display', 'is_overdue', 'days_assigned'
        ]


class AssignmentListSerializer(serializers.ModelSerializer):
    device_display = serializers.CharField(source='device.__str__', read_only=True)
    employee_display = serializers.CharField(source='employee.get_full_name', read_only=True)
    assigned_by_display = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    device = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id', 'device', 'employee', 'assigned_date', 'expected_return_date',
            'actual_return_date', 'status',
            'device_display', 'employee_display', 'assigned_by_display', 'status_display', 'is_overdue'
        ]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            'device', 'employee', 'expected_return_date',
            'purpose', 'notes', 'requires_approval'
        ]

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)