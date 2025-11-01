from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, AuditLog, SystemSettings, Location


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    assigned_devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'groups', 'linked_employee', 'assigned_devices_count', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'full_name', 'assigned_devices_count']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_assigned_devices_count(self, obj):
        # Check if user has linked employee and count their assigned devices
        if obj.linked_employee:
            return obj.linked_employee.assigned_devices.filter(status='assigned').count()
        return 0


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'groups', 'linked_employee'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Group validation based on current user
        current_user = self.context['request'].user
        target_groups = attrs.get('groups', [])
        
        # Check if current user can assign the requested groups
        for group in target_groups:
            # Users without system management cannot assign groups with system management permissions
            if not current_user.can_manage_system_settings and group.permissions.filter(codename='can_manage_system').exists():
                raise serializers.ValidationError("You don't have permission to assign this group")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        groups = validated_data.pop('groups', [])
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Assign groups
        if groups:
            user.groups.set(groups)
        
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'user_display']
    
    def get_user_display(self, obj):
        return obj.user.get_full_name() if obj.user else 'System'


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'code', 'description', 'address', 'building', 'floor', 'is_active']
        read_only_fields = ['id']