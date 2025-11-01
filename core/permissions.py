"""
Django REST Framework permissions for the DMP project.
Follows Django best practices for granular permission control.
"""
from rest_framework import permissions
from django.contrib.auth.models import Group


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Standard Django pattern for object-level permissions.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request,
        # Write permissions only to the owner of the snippet.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has an owner or user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission for admin-only write access.
    Standard pattern for admin-controlled resources.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_staff


class CanManageUsers(permissions.BasePermission):
    """
    Permission for user management functionality.
    Uses Django's built-in permission system.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user has custom permission or is admin
        return (
            request.user.has_perm('core.can_manage_users') or
            request.user.is_staff or
            request.user.groups.filter(name='User Managers').exists()
        )


class CanManageDevices(permissions.BasePermission):
    """
    Permission for device management functionality.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.has_perm('devices.can_manage_devices') or
            request.user.is_staff or
            request.user.groups.filter(name='Device Managers').exists()
        )


class CanViewReports(permissions.BasePermission):
    """
    Permission for viewing reports.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.has_perm('reports.can_view_reports') or
            request.user.is_staff or
            request.user.groups.filter(name='Report Viewers').exists()
        )


class CanManageAssignments(permissions.BasePermission):
    """
    Permission for assignment management.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.has_perm('assignments.can_manage_assignments') or
            request.user.is_staff or
            request.user.groups.filter(name='Assignment Managers').exists()
        )


class CanApproveRequests(permissions.BasePermission):
    """
    Permission for approval functionality.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            request.user.has_perm('approvals.can_approve_requests') or
            request.user.is_staff or
            request.user.groups.filter(name='Approvers').exists()
        )


class DepartmentBasedPermission(permissions.BasePermission):
    """
    Permission based on user's department.
    Standard pattern for department-based access control.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow access if user has employee profile with valid department
        if hasattr(request.user, 'employee_profile'):
            return bool(request.user.employee_profile.department)
        
        return request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow if same department or is staff
        if request.user.is_staff:
            return True
        
        if hasattr(request.user, 'employee_profile') and hasattr(obj, 'department'):
            return request.user.employee_profile.department == obj.department
        
        return False