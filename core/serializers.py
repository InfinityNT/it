from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, AuditLog, SystemSettings


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    assigned_devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'employee_id', 'department', 'phone', 'location',
            'is_active_employee', 'assigned_devices_count', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'full_name', 'assigned_devices_count']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_assigned_devices_count(self, obj):
        return obj.assigned_devices.filter(status='assigned').count()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'role', 'employee_id', 'department', 'phone', 'location', 'is_active_employee'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Role validation based on current user
        current_user = self.context['request'].user
        target_role = attrs.get('role', 'viewer')
        
        # Staff users cannot create superuser or staff roles
        if current_user.is_staff_role and target_role in ['superuser', 'staff']:
            raise serializers.ValidationError("You don't have permission to assign this role")
        
        # Only superusers can create other superusers
        if target_role == 'superuser' and not current_user.is_superuser_role:
            raise serializers.ValidationError("Only IT Managers can create other IT Manager accounts")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
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