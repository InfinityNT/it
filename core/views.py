from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import models, transaction
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.management import call_command
import subprocess
import os
from pathlib import Path
from datetime import datetime
from django.utils import timezone
import threading
from .models import User, AuditLog, SystemSettings, UserQuickAction, Location
from .decorators import permission_required_redirect




def _resolve_doc_path(doc_path):
    """Resolve a doc path safely, preventing directory traversal."""
    from django.conf import settings as django_settings
    docs_root = Path(django_settings.BASE_DIR) / 'docs'
    # Append .md if not present
    if not doc_path.endswith('.md'):
        doc_path = doc_path + '.md'
    resolved = (docs_root / doc_path).resolve()
    # Ensure path stays within docs root
    if not str(resolved).startswith(str(docs_root.resolve())):
        return None
    if not resolved.is_file():
        return None
    return resolved


def _extract_title(md_content):
    """Extract the first # heading from markdown content."""
    for line in md_content.split('\n'):
        line = line.strip()
        if line.startswith('# ') and not line.startswith('##'):
            return line[2:].strip()
    return None
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    AuditLogSerializer, SystemSettingsSerializer
)


@login_required
def user_list_api_view(request):
    """User list API that returns HTML"""
    queryset = User.objects.all()
    
    # Apply filters
    group = request.GET.get('group')
    department = request.GET.get('department')
    search = request.GET.get('search')
    
    if group:
        queryset = queryset.filter(groups__name=group)
    if department:
        queryset = queryset.filter(department__icontains=department)
    if search:
        queryset = queryset.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(employee_id__icontains=search)
        )
    
    # Add device count annotation - now using Employee relationship
    from django.db.models import Count, Case, When, IntegerField
    from employees.models import Employee
    
    users = queryset.annotate(
        assigned_devices_count=Case(
            When(employee_profile__isnull=False, then=Count('employee_profile__assigned_devices', filter=models.Q(employee_profile__assigned_devices__status='assigned'))),
            default=0,
            output_field=IntegerField()
        )
    ).order_by('username')
    
    # Redirect to dashboard which handles users via SPA
    return redirect('dashboard')


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        # Check if user has permission to manage users
        if not self.request.user.can_manage_users:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to create users")
        serializer.save()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        group = self.request.query_params.get('group')
        department = self.request.query_params.get('department')
        search = self.request.query_params.get('search')
        
        if group:
            queryset = queryset.filter(groups__name=group)
        if department:
            queryset = queryset.filter(department__icontains=department)
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(employee_id__icontains=search)
            )
        
        return queryset.order_by('username')


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        # Check if user has permission to manage users
        if not self.request.user.can_manage_users:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update users")
        
        # Additional permission validation for updates
        current_user = self.request.user
        target_user = self.get_object()
        
        # Users without system management cannot modify accounts with system management
        if not current_user.can_manage_system_settings and target_user.can_manage_system_settings:
            raise PermissionDenied("You cannot modify accounts with system management privileges")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check if user has permission to manage users
        if not self.request.user.can_manage_users:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to delete users")
        
        # Users without system management cannot delete accounts with system management
        if not self.request.user.can_manage_system_settings and instance.can_manage_system_settings:
            raise PermissionDenied("You cannot delete accounts with system management privileges")
        
        instance.delete()


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        user = self.request.query_params.get('user')  # Alternative parameter name for compatibility
        action = self.request.query_params.get('action')
        model_name = self.request.query_params.get('model_name')
        object_id = self.request.query_params.get('object_id')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        elif user:  # Support both 'user' and 'user_id' parameters
            queryset = queryset.filter(user_id=user)
        if action:
            queryset = queryset.filter(action=action)
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        
        return queryset


class SystemSettingsListView(generics.ListCreateAPIView):
    queryset = SystemSettings.objects.filter(is_active=True)
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]


class SystemSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def api_login_view(request):
    """Pure JSON API endpoint for authentication"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        
        # Check if password change is required
        password_change_required = user.needs_password_change if hasattr(user, 'needs_password_change') else False
        
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful',
            'password_change_required': password_change_required
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """HTML/HTMX login endpoint"""
    serializer = LoginSerializer(data=request.POST)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })
        response['HX-Redirect'] = '/'
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_logout_view(request):
    """Pure JSON API endpoint for logout"""
    logout(request)
    return Response({'message': 'Logout successful'})


@ensure_csrf_cookie
@login_required
def logout_view(request):
    """Handle logout for HTMX and regular requests (not pure API)"""
    if request.method == 'POST':
        logout(request)
        if request.headers.get('HX-Request'):
            # HTMX request - return redirect header
            response = JsonResponse({'message': 'Logout successful'})
            response['HX-Redirect'] = '/login/'
            return response
        else:
            # Regular request - redirect normally
            return redirect('login')
    
    # GET request - just redirect to login
    return redirect('login')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    return Response(UserSerializer(request.user).data)


# Traditional Django views for frontend
@login_required
def dashboard_view(request):
    """Dashboard view - main landing page after login"""
    context = {
        'user': request.user,
        'is_dashboard': True,  # Hides sidebar, enables full-width dashboard
    }

    return render(request, 'dashboard.html', context)


def login_page_view(request):
    """Login page view - shows standalone login page"""
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Show login page
    return render(request, 'login.html')


@permission_required_redirect('core.can_view_users', message='You do not have permission to view users.')
def users_view(request):
    """Users management view"""

    action = request.GET.get('action')
    if action == 'add':
        return redirect('add-user')

    return render(request, 'core/users.html')


@permission_required_redirect('core.can_modify_users', message='You do not have permission to add users.')
def add_user_view(request):
    """Add new user view"""
    
    if request.method == 'POST':
        try:
            # Create user
            password_change_required = request.POST.get('password_change_required', 'on') == 'on'  # Default to True
            
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                password=request.POST.get('password')
            )
            
            # Set password change requirement
            user.password_change_required = password_change_required
            
            # Assign user to selected group
            group_id = request.POST.get('groups')
            if group_id:
                from django.contrib.auth.models import Group
                try:
                    group = Group.objects.get(id=group_id)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    pass
            
            # Link to employee if selected
            linked_employee_id = request.POST.get('linked_employee')
            if linked_employee_id:
                from employees.models import Employee
                try:
                    employee = Employee.objects.get(id=linked_employee_id)
                    user.linked_employee = employee
                    # Update the employee's system_user field
                    employee.system_user = user
                    employee.save()
                except Employee.DoesNotExist:
                    pass
            
            user.is_active = True
            user.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='User',
                object_id=str(user.id),
                object_repr=str(user),
                changes={'created_by': request.user.get_full_name(), 'username': user.username},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if password_change_required:
                messages.success(request, f'User {user.get_full_name()} created successfully. They will be required to change their password on first login.')
            else:
                messages.success(request, f'User {user.get_full_name()} created successfully.')
            return redirect('users')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    # Get employees and groups for dropdown
    from employees.models import Employee
    from django.contrib.auth.models import Group
    
    employees = Employee.objects.filter(system_user__isnull=True).order_by('employee_id')
    
    # Get groups that current user can assign based on their permissions
    available_groups = []
    if request.user.has_perm('core.can_modify_users'):
        if request.user.can_manage_system_settings:
            # Users with system management can assign any group
            available_groups = Group.objects.all().order_by('name')
        else:
            # Users without system management cannot assign groups with system permissions
            available_groups = Group.objects.exclude(permissions__codename='can_manage_system').order_by('name')
    
    context = {
        'employees': employees,
        'available_groups': available_groups
    }
    # Redirect to dashboard where add user modal will handle this
    return redirect('dashboard')


@login_required
@permission_required_redirect('core.can_modify_users', message='You do not have permission to add users.')
def add_user_modal_view(request):
    """Render add user modal form for HTMX requests."""
    if request.method == 'GET':
        # Get employees and groups for dropdown
        from employees.models import Employee
        from django.contrib.auth.models import Group

        employees = Employee.objects.filter(system_user__isnull=True).order_by('employee_id')

        # Get groups that current user can assign based on their permissions
        available_groups = []
        if request.user.has_perm('core.can_modify_users'):
            if request.user.can_manage_system_settings:
                # Users with system management can assign any group
                available_groups = Group.objects.all().order_by('name')
            else:
                # Users without system management cannot assign groups with system permissions
                available_groups = Group.objects.exclude(permissions__codename='can_manage_system').order_by('name')

        context = {
            'employees': employees,
            'available_groups': available_groups
        }

        # If HTMX request, return modal template
        if request.headers.get('HX-Request'):
            return render(request, 'components/forms/add_user_modal.html', context)
        # Otherwise redirect to users page
        return redirect('users')

    # POST handling - reuse the existing add_user_view logic
    elif request.method == 'POST':
        # Call the existing add_user_view logic
        return add_user_view(request)


@login_required
def user_detail_view(request, user_id):
    """User detail view - returns modal for HTMX requests"""
    if not request.user.can_manage_users:
        messages.error(request, "You don't have permission to view user details.")
        return redirect('dashboard')

    user_detail = get_object_or_404(User, id=user_id)

    # Users without system management cannot view details of accounts with system management
    if not request.user.can_manage_system_settings and user_detail.can_manage_system_settings:
        messages.error(request, "You don't have permission to view details of accounts with system management privileges.")
        return redirect('users')

    context = {
        'user_detail': user_detail,
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'core/user_detail_modal.html', context)
    # Otherwise redirect to users page
    return redirect('users')


@login_required
def deactivate_user_modal_view(request, user_id):
    """Render deactivate user confirmation modal for HTMX requests."""
    # Check permission - only users with system management can deactivate users
    if not request.user.can_manage_system_settings:
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied. You do not have access to deactivate users.</div>',
            status=403
        )

    target_user = get_object_or_404(User, id=user_id)

    # Don't allow users to deactivate themselves
    if target_user == request.user:
        return render(request, 'components/forms/deactivate_user_modal.html', {
            'error_message': 'You cannot deactivate your own account.'
        })

    context = {
        'target_user': target_user,
    }

    return render(request, 'components/forms/deactivate_user_modal.html', context)


@login_required
def reactivate_user_modal_view(request, user_id):
    """Render reactivate user confirmation modal for HTMX requests."""
    # Check permission - only users with system management can reactivate users
    if not request.user.can_manage_system_settings:
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied. You do not have access to reactivate users.</div>',
            status=403
        )

    target_user = get_object_or_404(User, id=user_id)

    context = {
        'target_user': target_user,
    }

    return render(request, 'components/forms/reactivate_user_modal.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    
    # Only allow users with system management to toggle user status
    if not request.user.can_manage_system_settings:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Don't allow users to deactivate themselves
    if user == request.user:
        return Response({'error': 'You cannot deactivate your own account'}, status=status.HTTP_400_BAD_REQUEST)

    # Prevent deactivating the last active superuser
    if user.is_superuser and user.is_active:
        active_superusers = User.objects.filter(is_active=True, is_superuser=True).exclude(id=user.id)
        if active_superusers.count() == 0:
            return Response(
                {'error': 'Cannot deactivate the last active superuser. At least one superuser must remain active.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    user.is_active = not user.is_active
    user.save()
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='User',
        object_id=str(user.id),
        object_repr=str(user),
        changes={'status_changed': 'activated' if user.is_active else 'deactivated', 'changed_by': request.user.get_full_name()},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
        'is_active': user.is_active
    })


@ensure_csrf_cookie
@login_required
def user_edit_view(request, user_id):
    """User edit view"""
    if not request.user.can_manage_users:
        messages.error(request, "You don't have permission to edit users.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Users without system management cannot edit accounts with system management
    if not request.user.can_manage_system_settings and user.can_manage_system_settings:
        messages.error(request, "You don't have permission to edit accounts with system management privileges.")
        return redirect('users')
    
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                # Group validation for updates
                new_group_id = request.POST.get('groups')
                
                if new_group_id:
                    from django.contrib.auth.models import Group
                    try:
                        new_group = Group.objects.get(id=new_group_id)
                        # Users without system management cannot assign groups with system management permissions
                        if not request.user.can_manage_system_settings and new_group.permissions.filter(codename='can_manage_system').exists():
                            return JsonResponse({'error': "You don't have permission to assign this group"}, status=403)
                        
                        # Clear existing groups and assign new one
                        user.groups.clear()
                        user.groups.add(new_group)
                    except Group.DoesNotExist:
                        return JsonResponse({'error': "Selected group does not exist"}, status=400)
                
                # Update user information
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.email = request.POST.get('email')
                user.is_staff = request.POST.get('is_staff') == 'on'
                
                # Handle employee linking
                linked_employee_id = request.POST.get('linked_employee')
                if linked_employee_id:
                    from employees.models import Employee
                    try:
                        employee = Employee.objects.get(id=linked_employee_id)
                        # Clear previous employee link if exists
                        if user.linked_employee:
                            user.linked_employee.system_user = None
                            user.linked_employee.save()
                        user.linked_employee = employee
                        employee.system_user = user
                        employee.save()
                    except Employee.DoesNotExist:
                        pass
                else:
                    # Clear employee link if none selected
                    if user.linked_employee:
                        user.linked_employee.system_user = None
                        user.linked_employee.save()
                        user.linked_employee = None
                
                user.save()
                
                # Create audit log entry
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    model_name='User',
                    object_id=str(user.id),
                    object_repr=str(user),
                    changes={'updated_by': request.user.get_full_name(), 'username': user.username},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                response = JsonResponse({'message': 'User updated successfully'})
                response['HX-Redirect'] = f'/users/{user.id}/'
                return response
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            # Handle regular form submission
            messages.success(request, 'User updated successfully')
            return redirect('user-detail-page', user_id=user.id)
    
    # Get employees and groups for dropdown (exclude those already linked to other users)
    from employees.models import Employee
    from django.contrib.auth.models import Group
    
    employees = Employee.objects.filter(
        models.Q(system_user__isnull=True) | models.Q(system_user=user)
    ).order_by('employee_id')
    
    # Get groups that current user can assign based on their permissions
    available_groups = []
    if request.user.has_perm('core.can_modify_users'):
        if request.user.can_manage_system_settings:
            # Users with system management can assign any group
            available_groups = Group.objects.all().order_by('name')
        else:
            # Users without system management cannot assign groups with system permissions
            available_groups = Group.objects.exclude(permissions__codename='can_manage_system').order_by('name')
    
    context = {
        'user_profile': user,
        'employees': employees,
        'available_groups': available_groups
    }

    # If HTMX request, return modal template
    if request.headers.get('HX-Request'):
        return render(request, 'core/user_edit_modal.html', context)
    # Otherwise redirect to users page
    return redirect('users')


@login_required
def profile_settings_view(request):
    """Profile settings view - always shows personal settings"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            # Handle password change
            from django.contrib.auth import update_session_auth_hash
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password changed successfully.')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        else:
            # Handle profile update
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            messages.success(request, 'Profile updated successfully.')
    
    context = {
        'user': user,
        'page_title': 'Profile Settings',
        'can_manage_system': False,  # Profile page is personal settings only
        'available_actions': user.get_available_quick_actions()  # Include quick actions directly
    }

    # HTMX requests get the component template
    if request.headers.get('HX-Request'):
        return render(request, 'components/views/settings.html', context)
    else:
        # Non-HTMX requests get the full page
        return render(request, 'core/settings.html', context)


@login_required
def settings_view(request):
    """Settings view - content varies by user role"""
    user = request.user

    # Load current settings for display
    current_settings = {}
    last_backup_time = None
    if user.can_manage_system_settings:
        from core.models import SystemSettings
        settings_queryset = SystemSettings.objects.filter(is_active=True)
        for setting in settings_queryset:
            current_settings[setting.key] = setting.value

        # Get last backup time from audit log
        last_backup = AuditLog.objects.filter(model_name='Backup').order_by('-timestamp').first()
        if last_backup:
            last_backup_time = timezone.localtime(last_backup.timestamp).strftime('%b %d, %Y at %I:%M %p')

    context = {
        'user': user,
        'can_manage_system': user.can_manage_system_settings,
        'page_title': 'System Settings' if user.can_manage_system_settings else 'Profile Settings',
        'current_settings': current_settings,
        'last_backup_time': last_backup_time,
    }

    # If HTMX request, return content fragment
    if request.headers.get('HX-Request'):
        return render(request, 'components/views/settings.html', context)
    # If direct access, return full page
    else:
        return render(request, 'core/settings.html', context)


@login_required
def dashboard_stats_view(request):
    """Dashboard statistics API"""
    from devices.models import Device
    from assignments.models import Assignment
    
    total_devices = Device.objects.count()
    available_devices = Device.objects.filter(status='available').count()
    assigned_devices = Device.objects.filter(status='assigned').count()
    context = {
        'total_devices': total_devices,
        'available_devices': available_devices,
        'assigned_devices': assigned_devices,
    }
    
    return render(request, 'components/dashboard/stats.html', context)


@login_required
def dashboard_activity_view(request):
    """Recent activity API"""
    # Get recent audit log entries
    recent_logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    activities = []
    for log in recent_logs:
        user_name = log.user.get_full_name() if log.user else 'System'

        # Create readable description
        action_display = log.get_action_display()
        description = log.model_name
        if log.object_repr:
            description += f": {log.object_repr}"

        activities.append({
            'action': action_display,
            'description': description,
            'timestamp': log.timestamp.isoformat(),
            'user': user_name if user_name else log.user.username
        })
    
    # If no audit logs exist, show a placeholder
    if not activities:
        activities = [{
            'action': 'System',
            'description': 'No recent activity yet',
            'timestamp': timezone.now().isoformat(),
            'user': 'System'
        }]
    
    context = {'activities': activities}
    return render(request, 'components/dashboard/activity.html', context)


@login_required
def dashboard_quick_actions_view(request):
    """API to get user's quick actions for dashboard grid"""
    user = request.user
    enabled_actions = user.get_enabled_quick_actions()

    # Always include profile button as a quick action
    from collections import namedtuple
    QuickAction = namedtuple('QuickAction', ['code', 'display_name', 'icon', 'url', 'url_params'])
    profile_action = QuickAction(
        code='profile',
        display_name='My Profile',
        icon='bi bi-person-circle',
        url='/profile/',
        url_params=''
    )

    context = {
        'actions': enabled_actions,
        'profile_action': profile_action,
    }

    return render(request, 'components/dashboard/quick_actions_grid.html', context)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_search_view(request):
    """Global search API for devices"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({'results': []})
    
    from devices.models import Device
    from django.db.models import Q
    
    # Search across multiple device fields and related models
    # Optimize by prioritizing most common search patterns
    devices = Device.objects.select_related(
        'device_model__category', 
        'device_model', 
        'assigned_to'
    ).filter(
        Q(asset_tag__icontains=query) |  # Most common search
        Q(serial_number__icontains=query) |  # Second most common
        Q(device_model__manufacturer__icontains=query) |
        Q(device_model__model_name__icontains=query) |
        Q(device_model__category__name__icontains=query) |
        Q(assigned_to__first_name__icontains=query) |
        Q(assigned_to__last_name__icontains=query) |
        Q(assigned_to__email__icontains=query) |
        Q(location__icontains=query) |
        Q(vendor__icontains=query) |
        Q(notes__icontains=query) |
        Q(barcode__icontains=query)
    ).order_by(
        # Order by relevance: exact matches first, then partial matches
        models.Case(
            models.When(asset_tag__iexact=query, then=models.Value(1)),
            models.When(asset_tag__istartswith=query, then=models.Value(2)),
            models.When(serial_number__iexact=query, then=models.Value(3)),
            models.When(serial_number__istartswith=query, then=models.Value(4)),
            default=models.Value(5),
            output_field=models.IntegerField(),
        ),
        'asset_tag'
    )[:10]  # Limit to 10 results for performance
    
    results = []
    for device in devices:
        result = {
            'id': device.id,
            'asset_tag': device.asset_tag,
            'serial_number': device.serial_number,
            'manufacturer': device.device_model.manufacturer,
            'model_name': device.device_model.model_name,
            'category': device.device_model.category.name,
            'status': device.status,
            'status_display': device.get_status_display(),
            'location': device.location,
            'assigned_to': device.assigned_to.get_full_name() if device.assigned_to else None,
        }
        results.append(result)
    
    return Response({'results': results})


# Quick Actions Management Views
@login_required
def quick_actions_api_view(request):
    """API to get user's enabled quick actions for the sidebar"""
    user = request.user
    enabled_actions = user.get_enabled_quick_actions()
    
    context = {
        'actions': enabled_actions,
        'has_actions': len(enabled_actions) > 0
    }
    
    return render(request, 'components/quick_actions/sidebar.html', context)


@login_required
def quick_actions_config_api_view(request):
    """API to get user's quick actions configuration for settings page"""
    user = request.user
    available_actions = user.get_available_quick_actions()
    
    context = {
        'available_actions': available_actions,
        'user': user
    }
    
    return render(request, 'components/quick_actions/config_partial.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def quick_actions_toggle_api_view(request):
    """API to toggle quick action on/off"""
    user = request.user
    action_code = request.data.get('action_code') or request.POST.get('action_code')
    is_enabled = (request.data.get('is_enabled') or request.POST.get('is_enabled')) == 'true'
    
    if not action_code:
        return Response({'success': False, 'message': 'Action code is required'}, status=400)
    
    # Get or create the quick action
    user_action, created = UserQuickAction.objects.get_or_create(
        user=user,
        action_code=action_code,
        defaults={'is_enabled': is_enabled}
    )
    
    if not created:
        user_action.is_enabled = is_enabled
        user_action.save()
    
    return Response({
        'success': True,
        'message': f'Quick action {"enabled" if is_enabled else "disabled"} successfully'
    })


@login_required
def password_change_view(request):
    """Password change view for users who are required to change their password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate current password
        if not request.user.check_password(current_password):
            error_msg = 'Current password is incorrect.'
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'components/forms/password_change_modal.html')
        
        # Validate new passwords match
        if new_password1 != new_password2:
            error_msg = 'New passwords do not match.'
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'components/forms/password_change_modal.html')
        
        # Validate password strength using Django validators
        from django.contrib.auth.password_validation import validate_password
        try:
            validate_password(new_password1, request.user)
        except Exception as e:
            error_messages = list(e.messages) if hasattr(e, 'messages') else [str(e)]
            if request.headers.get('HX-Request'):
                return JsonResponse({'error': '; '.join(error_messages)}, status=400)
            for error in error_messages:
                messages.error(request, error)
            return render(request, 'components/forms/password_change_modal.html')
        
        # Change password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_name='User',
            object_id=str(request.user.id),
            object_repr=str(request.user),
            changes={'password_changed': True},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Handle HTMX requests from login page
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully!'
            })
        
        messages.success(request, 'Password changed successfully! You can now continue using the system.')
        return redirect('dashboard')
    
    # For HTMX requests (e.g. from profile settings), return content without modal wrapper
    if request.headers.get('HX-Request'):
        return render(request, 'components/forms/password_change_content.html')
    return render(request, 'components/forms/password_change_modal.html')


# API endpoints for SPA components
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def auth_form_view(request):
    """Return login form component"""
    return render(request, 'components/auth/login_form.html')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_component_view(request):
    """Return dashboard component"""
    context = {
        'user': request.user,
        'total_devices': 0,  # Will be populated by HTMX
        'available_devices': 0,
        'assigned_devices': 0,
        'breadcrumbs_list': [],  # Dashboard is home, no breadcrumbs needed
    }
    return render(request, 'components/views/dashboard.html', context)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def devices_component_view(request):
    """Return devices component"""
    context = {
        'user': request.user,
        'breadcrumbs_list': [
            {'name': 'Devices'},
        ]
    }
    return render(request, 'devices/devices_content.html', context)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def users_component_view(request):
    """Return users component"""
    context = {
        'user': request.user,
        'breadcrumbs_list': [
            {'name': 'Users'},
        ]
    }
    return render(request, 'components/views/users.html', context)


@login_required
def user_list_api_view(request):
    """Return user list as HTML cards for HTMX."""
    if not request.user.can_manage_users:
        return HttpResponse('<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> Permission denied. You do not have access to view users.</div>')

    # Get filter parameters
    search = request.GET.get('search', '').strip()
    role = request.GET.get('role', '').strip()
    department = request.GET.get('department', '').strip()

    # Track if any filters are active
    has_filters = bool(search or role or department)

    # Build queryset - show all users, active first
    users = User.objects.all()

    # Apply search filter
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )

    # Apply department filter (via linked employee)
    if department:
        users = users.filter(linked_employee__department__name__icontains=department)

    # Apply role filter (basic implementation)
    if role:
        if role == 'admin':
            users = users.filter(is_superuser=True)
        elif role == 'manager':
            users = users.filter(groups__permissions__codename='can_manage_system_settings').distinct()
        elif role == 'user':
            users = users.exclude(is_superuser=True).exclude(groups__permissions__codename='can_manage_system_settings').distinct()

    # Order by active status (active first), then username
    users = users.select_related('linked_employee', 'linked_employee__department').prefetch_related('groups').order_by('-is_active', 'username')

    # Check if database is empty (excluding current user who always exists)
    total_users = User.objects.count() if not users.exists() else None

    context = {
        'users': users,
        'user': request.user,
        'has_filters': has_filters,
        'is_empty_database': total_users == 0 if total_users is not None else False,
    }

    return render(request, 'components/users/list.html', context)


@csrf_exempt
@login_required
def reset_user_password(request, user_id):
    """Reset user password to a default value"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    
    # Only allow users with system management to reset passwords
    if not request.user.can_manage_system_settings:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Don't allow users to reset their own password this way
    if user == request.user:
        return JsonResponse({'error': 'You cannot reset your own password. Use the profile settings instead.'}, status=400)
    
    # Generate a temporary password
    import secrets
    import string
    
    # Generate a secure random password
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    # Set the new password
    user.set_password(temp_password)
    user.password_change_required = True  # Require user to change on next login
    user.save()
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='User',
        object_id=str(user.id),
        object_repr=str(user),
        changes={
            'password_reset_by': request.user.get_full_name(),
            'password_change_required': True
        },
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({
        'message': f'Password reset successfully for {user.get_full_name()}',
        'temporary_password': temp_password,
        'note': 'User will be required to change password on next login'
    })


@login_required
@login_required
@require_http_methods(["POST"])
def extend_session_view(request):
    """Extend the user's session by updating last_activity timestamp"""
    request.session['last_activity'] = timezone.now().timestamp()
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def save_settings_view(request):
    """Save system settings"""
    from django.http import JsonResponse
    from core.models import SystemSettings

    # Check permission
    if not request.user.can_manage_system_settings:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    settings_type = request.POST.get('settings_type')

    try:
        if settings_type == 'general':
            # Save general settings
            SystemSettings.objects.update_or_create(
                key='system_name',
                defaults={'value': request.POST.get('system_name', 'IT Device Management')}
            )
            SystemSettings.objects.update_or_create(
                key='timezone',
                defaults={'value': request.POST.get('timezone', 'UTC')}
            )
            message = 'General settings saved successfully'

        elif settings_type == 'backup':
            # Save backup settings
            SystemSettings.objects.update_or_create(
                key='backup_frequency',
                defaults={'value': request.POST.get('backup_frequency', 'daily')}
            )
            message = 'Backup settings saved successfully'

        elif settings_type == 'security':
            # Save security settings
            SystemSettings.objects.update_or_create(
                key='session_timeout',
                defaults={'value': request.POST.get('session_timeout', '30')}
            )
            SystemSettings.objects.update_or_create(
                key='password_policy',
                defaults={'value': request.POST.get('password_policy', 'standard')}
            )
            SystemSettings.objects.update_or_create(
                key='password_expiry',
                defaults={'value': request.POST.get('password_expiry', '90')}
            )
            message = 'Security settings saved successfully'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid settings type'}, status=400)

        # Log the change
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_name='SystemSettings',
            object_repr=f'{settings_type} settings',
            changes={'settings_type': settings_type},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return JsonResponse({'success': True, 'message': message})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error saving settings: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def run_backup_view(request):
    """Run database backup"""
    from django.http import JsonResponse
    import subprocess
    import os
    from datetime import datetime
    from django.conf import settings as django_settings

    # Check permission
    if not request.user.can_manage_system_settings:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    try:
        # Get database path from settings
        db_path = django_settings.DATABASES['default']['NAME']

        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp (use local time from configured timezone)
        from django.utils import timezone as tz
        now = tz.localtime(tz.now())
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')

        # Copy database file
        import shutil
        shutil.copy2(db_path, backup_file)

        # Log the backup
        AuditLog.objects.create(
            user=request.user,
            action='create',
            model_name='Backup',
            object_repr=f'Database backup {timestamp}',
            changes={'backup_file': backup_file},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # Format timestamp for display
        backup_time_display = now.strftime('%b %d, %Y at %I:%M %p')

        return JsonResponse({
            'success': True,
            'message': f'Backup created successfully: {os.path.basename(backup_file)}',
            'last_backup_time': backup_time_display
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Backup failed: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def check_data_integrity_view(request):
    """Check database integrity"""
    from django.http import JsonResponse
    from django.core import management
    import io

    # Check permission
    if not request.user.can_manage_system_settings:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)

    try:
        # Run integrity check
        out = io.StringIO()
        management.call_command('check_data_integrity', '--verbose', stdout=out)
        output = out.getvalue()

        # Count issues (simple heuristic - look for "inconsistency" or "error" in output)
        issues_found = output.lower().count('inconsistency') + output.lower().count('error')

        # Log the check
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_name='System',
            object_repr='Data integrity check',
            changes={'issues_found': issues_found, 'output': output[:500]},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        message = 'Data integrity check completed'
        if issues_found > 0:
            message += f'. Found {issues_found} potential issue(s). Check audit logs for details.'
        else:
            message += '. No issues found.'

        return JsonResponse({
            'success': True,
            'message': message,
            'issues_found': issues_found
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Integrity check failed: {str(e)}'
        }, status=500)


@login_required
def add_location_modal_view(request):
    """Render the add location modal and handle form submission"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()

        errors = []
        if not name:
            errors.append('Location name is required.')
        if not code:
            errors.append('Location code is required.')

        if errors:
            return render(request, 'core/partials/location_add_form.html', {
                'error': ' '.join(errors)
            })

        # Check if location name or code already exists
        if Location.objects.filter(name__iexact=name).exists():
            return render(request, 'core/partials/location_add_form.html', {
                'error': f'A location named "{name}" already exists.'
            })
        if Location.objects.filter(code__iexact=code).exists():
            return render(request, 'core/partials/location_add_form.html', {
                'error': f'A location with code "{code}" already exists.'
            })

        try:
            location = Location.objects.create(
                name=name,
                code=code
            )
            messages.success(request, f'Location "{location.name}" created successfully.')
            # Return the modal view with list
            return render(request, 'core/manage_locations_modal.html', {
                'can_modify': request.user.can_manage_system_settings,
            })
        except Exception as e:
            return render(request, 'core/partials/location_add_form.html', {
                'error': f'Error creating location: {str(e)}'
            })

    # GET request - render add form
    return render(request, 'core/partials/location_add_form.html')


@login_required
def manage_locations_add_form_view(request):
    """Render the add location form (replaces list view)"""
    return render(request, 'core/partials/location_add_form.html')


# ==========================================
#   MANAGE LOCATIONS VIEWS
# ==========================================

@login_required
def manage_locations_view(request):
    """Render the manage locations modal"""
    return render(request, 'core/manage_locations_modal.html', {
        'can_modify': request.user.can_manage_system_settings,
    })


@login_required
def manage_locations_list_view(request):
    """Return location list for HTMX partial updates"""
    from django.db import models as db_models
    search = request.GET.get('search', '').strip()
    locations = Location.objects.all()

    if search:
        locations = locations.filter(
            db_models.Q(name__icontains=search) |
            db_models.Q(code__icontains=search) |
            db_models.Q(building__icontains=search) |
            db_models.Q(address__icontains=search)
        )

    locations = locations.order_by('name')

    return render(request, 'core/partials/location_list.html', {
        'locations': locations,
        'can_modify': request.user.can_manage_system_settings,
    })


@login_required
@permission_required('core.can_manage_system', raise_exception=True)
def manage_locations_edit_view(request, location_id):
    """Edit a location inline"""
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        is_active = request.POST.get('is_active') == 'on'

        errors = []
        if not name:
            errors.append('Location name is required.')
        if not code:
            errors.append('Location code is required.')

        if errors:
            return render(request, 'core/partials/location_edit_form.html', {
                'location': location,
                'error': ' '.join(errors),
            })

        # Check for duplicates (excluding current)
        if Location.objects.filter(name__iexact=name).exclude(id=location_id).exists():
            return render(request, 'core/partials/location_edit_form.html', {
                'location': location,
                'error': f'A location named "{name}" already exists.',
            })
        if Location.objects.filter(code__iexact=code).exclude(id=location_id).exists():
            return render(request, 'core/partials/location_edit_form.html', {
                'location': location,
                'error': f'A location with code "{code}" already exists.',
            })

        try:
            location.name = name
            location.code = code
            location.is_active = is_active
            location.save()
            messages.success(request, f'Location "{location.name}" updated successfully.')
            return manage_locations_list_view(request)
        except Exception as e:
            return render(request, 'core/partials/location_edit_form.html', {
                'location': location,
                'error': f'Error updating location: {str(e)}',
            })

    # GET - return edit form
    return render(request, 'core/partials/location_edit_form.html', {
        'location': location,
    })


@login_required
@permission_required('core.can_manage_system', raise_exception=True)
def manage_locations_delete_view(request, location_id):
    """Delete a location with confirmation"""
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        location_name = location.name
        location.delete()
        messages.success(request, f'Location "{location_name}" deleted successfully.')
        return manage_locations_list_view(request)

    # GET - return confirmation dialog
    return render(request, 'components/common/delete_confirmation.html', {
        'item': location,
        'item_id': f'location-item-{location.id}',
        'item_name': location.name,
        'list_target_id': 'locations-list',
        'delete_url': reverse('manage-locations-delete', args=[location_id]),
        'cancel_url': reverse('manage-locations-list'),
    })


# ==========================================
#   DOCS / HELP VIEWS
# ==========================================

@login_required
def docs_view(request):
    """Full-page Help Center landing."""
    return render(request, 'docs/docs.html')


@login_required
def docs_content_view(request):
    """HTMX content-only Help Center landing."""
    return render(request, 'docs/docs_content.html')


_DOCS_NAVIGATION_CACHE = None


def _get_docs_navigation():
    """Return docs navigation structure, cached after first call."""
    global _DOCS_NAVIGATION_CACHE
    if _DOCS_NAVIGATION_CACHE is not None:
        return _DOCS_NAVIGATION_CACHE
    _DOCS_NAVIGATION_CACHE = [
        {
            'title': 'User Guide',
            'icon': 'bi-book',
            'section': 'user-guide',
            'items': [
                {'title': 'Overview', 'path': 'user-guide/index'},
                {'title': 'Dashboard', 'path': 'user-guide/dashboard'},
                {'title': 'Devices', 'path': 'user-guide/devices'},
                {'title': 'Assignments', 'path': 'user-guide/assignments'},
                {'title': 'Employees', 'path': 'user-guide/employees'},
                {'title': 'Reports', 'path': 'user-guide/reports'},
                {'title': 'Approvals', 'path': 'user-guide/approvals'},
                {'title': 'Search', 'path': 'user-guide/search'},
            ],
        },
        {
            'title': 'Admin Guide',
            'icon': 'bi-gear',
            'section': 'admin-guide',
            'items': [
                {'title': 'Overview', 'path': 'admin-guide/index'},
                {'title': 'User Management', 'path': 'admin-guide/user-management'},
                {'title': 'System Settings', 'path': 'admin-guide/system-settings'},
                {'title': 'Locations', 'path': 'admin-guide/locations'},
                {'title': 'Categories & Models', 'path': 'admin-guide/categories-models'},
                {'title': 'Departments', 'path': 'admin-guide/departments'},
            ],
        },
        {
            'title': 'Developer',
            'icon': 'bi-code-slash',
            'section': 'developer',
            'items': [
                {'title': 'Overview', 'path': 'developer/index'},
                {'title': 'Quick Start', 'path': 'developer/quick-start'},
                {'title': 'Development Setup', 'path': 'developer/development-setup'},
                {'title': 'Project Structure', 'path': 'developer/project-structure'},
                {'title': 'Template System', 'path': 'developer/template-system'},
                {'title': 'Custom Reports', 'path': 'developer/custom-reports'},
                {'title': 'Production Deployment', 'path': 'developer/production-deployment'},
                {'title': 'Testing Guide', 'path': 'developer/testing-guide'},
            ],
        },
    ]
    return _DOCS_NAVIGATION_CACHE


@login_required
def docs_page_view(request, doc_path):
    """Render an individual markdown doc page."""
    import re as re_module
    import markdown as md_lib
    from django.http import Http404

    # Restrict admin-guide, developer, and CHANGELOG to system managers
    restricted_prefixes = ('admin-guide', 'developer', 'CHANGELOG')
    if doc_path.startswith(restricted_prefixes) and not request.user.can_manage_system_settings:
        raise Http404("Documentation page not found.")

    file_path = _resolve_doc_path(doc_path)
    if file_path is None:
        raise Http404("Documentation page not found.")

    raw = file_path.read_text(encoding='utf-8')

    # Size guard for very large files (e.g. CHANGELOG)
    truncated = False
    if len(raw) > 100_000:
        lines = raw.split('\n')[:500]
        raw = '\n'.join(lines)
        truncated = True

    title = _extract_title(raw) or doc_path.replace('/', ' - ').replace('-', ' ').title()

    # Render markdown
    md = md_lib.Markdown(extensions=['fenced_code', 'tables', 'toc'])
    html_content = md.convert(raw)
    toc_html = getattr(md, 'toc', '')

    # Rewrite relative .md links to /docs/ URLs
    # Resolve relative links against the current doc's directory
    import posixpath
    doc_dir = posixpath.dirname(doc_path.rstrip('/'))

    def _rewrite_md_link(m):
        target = m.group(1)
        if target.startswith('/') or '://' in target:
            return 'href="/docs/%s/"' % target.lstrip('/').removesuffix('.md')
        resolved = posixpath.normpath(posixpath.join(doc_dir, target)) if doc_dir else target
        return 'href="/docs/%s/"' % resolved

    html_content = re_module.sub(
        r'href="([^"]*?)\.md"',
        _rewrite_md_link,
        html_content,
    )

    # Determine current path key for sidebar active state
    current_path = doc_path.rstrip('/')
    if current_path.endswith('.md'):
        current_path = current_path[:-3]

    # Filter navigation sections based on permissions
    docs_nav = _get_docs_navigation()
    if not request.user.can_manage_system_settings:
        docs_nav = [s for s in docs_nav if s['section'] not in ('admin-guide', 'developer')]

    context = {
        'title': title,
        'html_content': html_content,
        'toc_html': toc_html,
        'truncated': truncated,
        'docs_nav': docs_nav,
        'current_path': current_path,
    }
    return render(request, 'docs/docs_page.html', context)
