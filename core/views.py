from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.management import call_command
import subprocess
import os
from pathlib import Path
from datetime import datetime
import threading
from .models import User, AuditLog, SystemSettings
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    AuditLogSerializer, SystemSettingsSerializer
)


@login_required
def user_list_api_view(request):
    """User list API that returns HTML"""
    queryset = User.objects.filter(is_active=True)
    
    # Apply filters
    role = request.GET.get('role')
    department = request.GET.get('department')
    search = request.GET.get('search')
    
    if role:
        queryset = queryset.filter(role=role)
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
    
    # Add device count annotation
    from django.db.models import Count
    users = queryset.annotate(
        assigned_devices_count=Count('assigned_devices', filter=models.Q(assigned_devices__status='assigned'))
    ).order_by('username')
    
    context = {'users': users}
    return render(request, 'core/user_list.html', context)


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
        role = self.request.query_params.get('role')
        department = self.request.query_params.get('department')
        search = self.request.query_params.get('search')
        
        if role:
            queryset = queryset.filter(role=role)
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
        
        # Additional role validation for updates
        current_user = self.request.user
        target_user = self.get_object()
        new_role = serializer.validated_data.get('role', target_user.role)
        
        # Staff users cannot modify superuser accounts or assign staff/superuser roles
        if current_user.is_staff_role:
            if target_user.is_superuser_role:
                raise PermissionDenied("You cannot modify IT Manager accounts")
            if new_role in ['superuser', 'staff']:
                raise PermissionDenied("You don't have permission to assign this role")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check if user has permission to manage users
        if not self.request.user.can_manage_users:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to delete users")
        
        # Staff users cannot delete superuser accounts
        if self.request.user.is_staff_role and instance.is_superuser_role:
            raise PermissionDenied("You cannot delete IT Manager accounts")
        
        instance.delete()


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        action = self.request.query_params.get('action')
        model_name = self.request.query_params.get('model_name')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
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
def login_view(request):
    if request.content_type == 'application/json':
        serializer = LoginSerializer(data=request.data)
    else:
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


@ensure_csrf_cookie
@login_required
def logout_view(request):
    """Handle logout for both regular and HTMX requests"""
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
    """Main dashboard view"""
    context = {
        'user': request.user,
        'total_devices': 0,  # Will be populated by HTMX
        'available_devices': 0,
        'assigned_devices': 0,
        'maintenance_requests': 0,
    }
    return render(request, 'core/dashboard.html', context)


def login_page_view(request):
    """Login page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/login.html')


@login_required
def users_view(request):
    """Users management view"""
    if not request.user.can_manage_users:
        messages.error(request, "You don't have permission to access user management.")
        return redirect('dashboard')
    return render(request, 'core/users.html')


@login_required
def user_detail_view(request, user_id):
    """User detail view"""
    if not request.user.can_manage_users:
        messages.error(request, "You don't have permission to view user details.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Staff users cannot view superuser details
    if request.user.is_staff_role and user.is_superuser_role:
        messages.error(request, "You don't have permission to view IT Manager details.")
        return redirect('users')
    
    context = {'user_profile': user}
    return render(request, 'core/user_detail.html', context)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    
    # Only allow admins or managers to toggle user status
    if request.user.role not in ['admin', 'manager']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Don't allow users to deactivate themselves
    if user == request.user:
        return Response({'error': 'You cannot deactivate your own account'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.is_active = not user.is_active
    user.save()
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='updated',
        model_name='User',
        object_id=user.id,
        changes=f'User {user.username} {"activated" if user.is_active else "deactivated"} by {request.user.get_full_name()}'
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
    
    # Staff users cannot edit superuser accounts
    if request.user.is_staff_role and user.is_superuser_role:
        messages.error(request, "You don't have permission to edit IT Manager accounts.")
        return redirect('users')
    
    if request.method == 'POST':
        if request.headers.get('HX-Request'):
            # Handle HTMX form submission
            try:
                # Role validation for updates
                new_role = request.POST.get('role')
                if request.user.is_staff_role and new_role in ['superuser', 'staff']:
                    return JsonResponse({'error': "You don't have permission to assign this role"}, status=403)
                
                # Update user information
                user.first_name = request.POST.get('first_name', '')
                user.last_name = request.POST.get('last_name', '')
                user.email = request.POST.get('email')
                user.employee_id = request.POST.get('employee_id', '')
                user.role = new_role
                user.is_active = request.POST.get('is_active') == 'on'
                user.is_staff = request.POST.get('is_staff') == 'on'
                user.save()
                
                # Create audit log entry
                AuditLog.objects.create(
                    user=request.user,
                    action='updated',
                    model_name='User',
                    object_id=user.id,
                    changes=f'User {user.username} updated by {request.user.get_full_name()}'
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
    
    context = {'user_profile': user}
    return render(request, 'core/user_edit.html', context)


@login_required
def settings_view(request):
    """Settings view - content varies by user role"""
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
            user.department = request.POST.get('department', '')
            user.phone = request.POST.get('phone', '')
            user.location = request.POST.get('location', '')
            user.save()
            messages.success(request, 'Profile updated successfully.')
    
    context = {
        'user': user,
        'can_manage_system': user.can_manage_system_settings,
    }
    
    if user.can_manage_system_settings:
        # Superuser sees system settings
        template = 'core/system_settings.html'
        context['page_title'] = 'System Settings'
    else:
        # Staff and viewers see profile settings
        template = 'core/profile_settings.html' 
        context['page_title'] = 'Profile Settings'
    
    return render(request, template, context)


@login_required
def dashboard_stats_view(request):
    """Dashboard statistics API"""
    from devices.models import Device
    from assignments.models import Assignment, MaintenanceRequest
    
    total_devices = Device.objects.count()
    available_devices = Device.objects.filter(status='available').count()
    assigned_devices = Device.objects.filter(status='assigned').count()
    maintenance_requests = MaintenanceRequest.objects.filter(status__in=['pending', 'approved', 'in_progress']).count()
    
    context = {
        'total_devices': total_devices,
        'available_devices': available_devices,
        'assigned_devices': assigned_devices,
        'maintenance_requests': maintenance_requests
    }
    
    return render(request, 'core/dashboard_stats.html', context)


@login_required
def dashboard_activity_view(request):
    """Recent activity API"""
    activities = [
        {
            'action': 'Device Assignment',
            'description': 'No recent activity yet',
            'timestamp': '2024-01-01T00:00:00Z',
            'user': 'System'
        }
    ]
    
    context = {'activities': activities}
    return render(request, 'core/dashboard_activity.html', context)


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


# Reports Views
@login_required
def reports_view(request):
    """Reports dashboard page"""
    return render(request, 'reports/reports.html')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_summary_view(request):
    """Summary statistics for reports dashboard"""
    from devices.models import Device
    from assignments.models import Assignment
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    devices = Device.objects.all()
    
    # Calculate total asset value
    total_value = devices.filter(purchase_price__isnull=False).aggregate(
        total=Sum('purchase_price')
    )['total'] or 0
    
    # Calculate utilization rate (assigned/total devices)
    total_devices = devices.count()
    assigned_devices = devices.filter(status='assigned').count()
    utilization_rate = (assigned_devices / total_devices * 100) if total_devices > 0 else 0
    
    # Calculate average assignment duration
    assignments = Assignment.objects.filter(status='returned')
    avg_duration = assignments.aggregate(
        avg=Avg(models.F('actual_return_date') - models.F('assigned_date'))
    )['avg']
    avg_duration_days = avg_duration.days if avg_duration else 0
    
    # Warranty expiring soon (next 30 days)
    thirty_days_from_now = timezone.now().date() + timedelta(days=30)
    warranty_expiring = devices.filter(
        warranty_expiry__lte=thirty_days_from_now,
        warranty_expiry__gt=timezone.now().date()
    ).count()
    
    summary_data = {
        'total_asset_value': f'${total_value:,.2f}',
        'utilization_rate': f'{utilization_rate:.1f}%',
        'avg_assignment_duration': f'{avg_duration_days} days',
        'warranty_expiring': warranty_expiring
    }
    
    html = f"""
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                                Total Asset Value
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                {summary_data['total_asset_value']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-currency-dollar fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-success shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                                Utilization Rate
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                {summary_data['utilization_rate']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-percent fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-info shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                                Avg Assignment Duration
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                {summary_data['avg_assignment_duration']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-clock fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-warning shadow h-100 py-2">
                <div class="card-body">
                    <div class="row no-gutters align-items-center">
                        <div class="col mr-2">
                            <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                                Warranty Expiring
                            </div>
                            <div class="h5 mb-0 font-weight-bold text-gray-800">
                                {summary_data['warranty_expiring']}
                            </div>
                        </div>
                        <div class="col-auto">
                            <i class="bi bi-exclamation-triangle fa-2x text-gray-300"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """
    
    return render(request, 'core/reports_summary.html', {'html_content': html})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_charts_view(request):
    """Chart data for reports dashboard"""
    from devices.models import Device, DeviceCategory
    from assignments.models import Assignment
    from django.db.models import Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Device distribution by category
    category_data = DeviceCategory.objects.annotate(
        device_count=Count('devicemodel__device')
    ).filter(device_count__gt=0)
    
    device_distribution = {
        'labels': [cat.name for cat in category_data],
        'values': [cat.device_count for cat in category_data]
    }
    
    # Status overview
    status_data = Device.objects.values('status').annotate(count=Count('id'))
    status_overview = {
        'labels': [item['status'].title() for item in status_data],
        'values': [item['count'] for item in status_data]
    }
    
    # Assignment trends (last 12 months)
    months = []
    assignments_data = []
    returns_data = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_assignments = Assignment.objects.filter(
            assigned_date__gte=month_start.date(),
            assigned_date__lte=month_end.date()
        ).count()
        
        month_returns = Assignment.objects.filter(
            actual_return_date__gte=month_start.date(),
            actual_return_date__lte=month_end.date()
        ).count()
        
        months.insert(0, month_start.strftime('%b %Y'))
        assignments_data.insert(0, month_assignments)
        returns_data.insert(0, month_returns)
    
    assignment_trends = {
        'labels': months,
        'assignments': assignments_data,
        'returns': returns_data
    }
    
    return Response({
        'device_distribution': device_distribution,
        'status_overview': status_overview,
        'assignment_trends': assignment_trends
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reports_top_users_view(request):
    """Top device users data"""
    from django.db.models import Count
    
    top_users = User.objects.annotate(
        device_count=Count('assigned_devices')
    ).filter(device_count__gt=0).order_by('-device_count')[:10]
    
    users_data = []
    for user in top_users:
        users_data.append({
            'name': user.get_full_name(),
            'email': user.email,
            'device_count': user.device_count
        })
    
    return Response({'users': users_data})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reports_generate_view(request, report_type):
    """Generate and download reports"""
    from django.http import HttpResponse
    from datetime import datetime
    import csv
    
    # For now, return CSV data - in production you might want PDF generation
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'inventory':
        from devices.models import Device
        writer.writerow(['Asset Tag', 'Serial Number', 'Category', 'Manufacturer', 'Model', 'Status', 'Location', 'Purchase Date', 'Purchase Price'])
        
        devices = Device.objects.select_related('device_model__category', 'device_model')
        for device in devices:
            writer.writerow([
                device.asset_tag,
                device.serial_number,
                device.device_model.category.name,
                device.device_model.manufacturer,
                device.device_model.model_name,
                device.get_status_display(),
                device.location,
                device.purchase_date.strftime('%Y-%m-%d') if device.purchase_date else '',
                f'${device.purchase_price}' if device.purchase_price else ''
            ])
    
    elif report_type == 'assignments':
        from assignments.models import Assignment
        writer.writerow(['Device', 'User', 'Assigned Date', 'Return Date', 'Status', 'Assigned By'])
        
        assignments = Assignment.objects.select_related('device', 'user', 'assigned_by')
        for assignment in assignments:
            writer.writerow([
                assignment.device.asset_tag,
                assignment.user.get_full_name(),
                assignment.assigned_date.strftime('%Y-%m-%d'),
                assignment.actual_return_date.strftime('%Y-%m-%d') if assignment.actual_return_date else '',
                assignment.get_status_display(),
                assignment.assigned_by.get_full_name()
            ])
    
    else:
        # Generic report with basic device info
        writer.writerow(['Report Type', 'Generated Date'])
        writer.writerow([report_type.title(), datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    
    return response
