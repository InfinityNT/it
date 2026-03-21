"""
Reusable mixins for Django apps following best practices.
Includes both bulk operations and standard Django patterns.
"""

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from functools import wraps
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form view.
    Standard Django pattern for AJAX handling.
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(form.errors, status=400)
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = {
                'pk': self.object.pk if hasattr(self, 'object') else None,
                'success': True,
                'message': 'Operation completed successfully'
            }
            return JsonResponse(data)
        return response


class MessagesContextMixin:
    """
    Mixin to add messages to context.
    Standard pattern for message handling in class-based views.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = messages.get_messages(self.request)
        return context


class DepartmentFilterMixin:
    """
    Mixin to filter querysets by user's department.
    Reusable pattern for department-based filtering.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.request.user.is_staff:
            return queryset
        
        if hasattr(self.request.user, 'employee_profile'):
            department = self.request.user.employee_profile.department
            if department and hasattr(queryset.model, 'department'):
                return queryset.filter(department=department)
        
        return queryset.none()


class AuditLogMixin:
    """
    Mixin to automatically create audit logs for model changes.
    Standard pattern for audit trail functionality.
    """
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create audit log entry
        from .models import AuditLog
        
        action = 'CREATE' if self.object._state.adding else 'UPDATE'
        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            model_name=self.object._meta.model_name,
            object_id=self.object.pk,
            object_repr=str(self.object),
            changes=self._get_changes(form) if hasattr(self, '_get_changes') else {}
        )
        
        return response
    
    def _get_changes(self, form):
        """Get the changes made to the object"""
        changes = {}
        if form.changed_data:
            for field in form.changed_data:
                changes[field] = {
                    'old': getattr(self.object, field, None),
                    'new': form.cleaned_data.get(field)
                }
        return changes


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """
    Enhanced version of Django's PermissionRequiredMixin.
    Provides better error messages and redirect handling.
    """
    login_url = reverse_lazy('login')
    permission_denied_message = "You don't have permission to access this page."
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
        return super().handle_no_permission()


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires admin access.
    Standard pattern for admin-only views.
    """
    login_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.is_staff:
            messages.error(request, "Admin access required.")
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires staff access.
    """
    login_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Staff access required.")
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class HtmxResponseMixin:
    """
    Mixin for HTMX response handling.
    Standard pattern for HTMX integration in Django.
    """
    def render_to_response(self, context, **response_kwargs):
        if hasattr(self.request, 'htmx') and self.request.htmx:
            # Return partial template for HTMX requests
            self.template_name = getattr(self, 'htmx_template_name', self.template_name)
        
        return super().render_to_response(context, **response_kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_htmx'] = bool(getattr(self.request, 'htmx', False))
        return context


def ajax_required(view_func):
    """
    Decorator that ensures the request is an AJAX request.
    Standard pattern for AJAX-only views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required_api(permission):
    """
    Decorator for API views that require specific permissions.
    Standard pattern for permission-based API access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            if not request.user.has_perm(permission):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator