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


class BulkOperationsMixin:
    """
    Mixin for handling bulk operations with standardized patterns
    """
    
    # Must be defined in subclasses
    bulk_model = None
    bulk_id_field = 'id'
    bulk_operations = {}
    
    def get_bulk_queryset(self, item_ids):
        """Get queryset for bulk operations"""
        if not self.bulk_model:
            raise NotImplementedError("bulk_model must be defined")
        
        filter_kwargs = {f"{self.bulk_id_field}__in": item_ids}
        return self.bulk_model.objects.filter(**filter_kwargs)
    
    def validate_bulk_request(self, request):
        """Validate bulk operation request"""
        item_ids = request.data.get('item_ids', [])
        operation = request.data.get('operation')
        
        if not item_ids:
            return Response(
                {'error': 'Item IDs are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not operation:
            return Response(
                {'error': 'Operation is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if operation not in self.bulk_operations:
            return Response(
                {'error': f'Invalid operation: {operation}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None
    
    def check_bulk_permissions(self, request, operation):
        """Check permissions for bulk operation"""
        operation_config = self.bulk_operations.get(operation, {})
        required_permission = operation_config.get('permission')
        
        if required_permission and not request.user.has_perm(required_permission):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return None
    
    def execute_bulk_operation(self, request):
        """Main bulk operation handler"""
        # Validate request
        validation_error = self.validate_bulk_request(request)
        if validation_error:
            return validation_error
        
        item_ids = request.data.get('item_ids', [])
        operation = request.data.get('operation')
        
        # Check permissions
        permission_error = self.check_bulk_permissions(request, operation)
        if permission_error:
            return permission_error
        
        # Get items
        items = self.get_bulk_queryset(item_ids)
        if not items.exists():
            return Response(
                {'error': 'No valid items found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Execute operation
        try:
            with transaction.atomic():
                result = self.perform_bulk_operation(request, operation, items)
                return Response(result)
        except Exception as e:
            logger.error(f"Bulk operation {operation} failed: {str(e)}")
            return Response(
                {'error': f'Bulk operation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_bulk_operation(self, request, operation, items):
        """Perform the actual bulk operation - to be implemented by subclasses"""
        operation_config = self.bulk_operations[operation]
        handler_method = getattr(self, f"handle_{operation}", None)
        
        if not handler_method:
            raise NotImplementedError(f"Handler for operation '{operation}' not implemented")
        
        return handler_method(request, items)
    
    def create_audit_log(self, request, operation, item, details=None):
        """Create audit log entry - can be overridden by subclasses"""
        pass
    
    def format_success_response(self, updated_count, errors=None, operation=None):
        """Format standardized success response"""
        response = {
            'success': True,
            'message': f'Successfully updated {updated_count} items',
            'updated_count': updated_count
        }
        
        if errors:
            response['errors'] = errors
            response['message'] += f' with {len(errors)} warnings'
        
        if operation:
            response['operation'] = operation
        
        return response


class StandardBulkOperationsView(BulkOperationsMixin, PermissionRequiredMixin):
    """
    Standard view for bulk operations with common patterns
    """
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests for bulk operations"""
        return self.execute_bulk_operation(request)
    
    def handle_update_status(self, request, items):
        """Standard status update handler"""
        new_status = request.data.get('new_status')
        if not new_status:
            raise ValueError("new_status is required")
        
        # Validate status value
        if hasattr(self.bulk_model, 'STATUS_CHOICES'):
            valid_statuses = dict(self.bulk_model.STATUS_CHOICES)
            if new_status not in valid_statuses:
                raise ValueError(f"Invalid status: {new_status}")
        
        updated_count = 0
        errors = []
        
        for item in items:
            try:
                old_status = getattr(item, 'status', None)
                setattr(item, 'status', new_status)
                item.save()
                
                # Create audit log
                self.create_audit_log(
                    request, 
                    'update_status', 
                    item, 
                    f'Status changed from {old_status} to {new_status}'
                )
                
                updated_count += 1
            except Exception as e:
                errors.append(f"Failed to update {item}: {str(e)}")
        
        return self.format_success_response(updated_count, errors, 'update_status')
    
    def handle_update_field(self, request, items, field_name, field_label=None):
        """Generic field update handler"""
        new_value = request.data.get(f'new_{field_name}')
        if new_value is None:
            raise ValueError(f"new_{field_name} is required")
        
        updated_count = 0
        errors = []
        field_display = field_label or field_name.replace('_', ' ').title()
        
        for item in items:
            try:
                old_value = getattr(item, field_name, None)
                setattr(item, field_name, new_value)
                item.save()
                
                # Create audit log
                self.create_audit_log(
                    request, 
                    f'update_{field_name}', 
                    item, 
                    f'{field_display} changed from {old_value} to {new_value}'
                )
                
                updated_count += 1
            except Exception as e:
                errors.append(f"Failed to update {item}: {str(e)}")
        
        return self.format_success_response(updated_count, errors, f'update_{field_name}')


def bulk_operation_view(model_class, operations_config, permission_required=None):
    """
    Decorator/factory function to create bulk operation views
    """
    def decorator(view_func):
        @api_view(['POST'])
        @permission_classes([IsAuthenticated])
        def wrapped_view(request, *args, **kwargs):
            # Create a temporary mixin instance
            class TempBulkView(BulkOperationsMixin):
                bulk_model = model_class
                bulk_operations = operations_config
                
                def has_permission(self):
                    if permission_required:
                        return request.user.has_perm(permission_required)
                    return True
            
            temp_view = TempBulkView()
            
            # Check permissions
            if not temp_view.has_permission():
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Execute bulk operation
            return temp_view.execute_bulk_operation(request)
        
        return wrapped_view
    return decorator