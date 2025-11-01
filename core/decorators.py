
from django.conf import settings
from django.contrib.auth.decorators import login_required as django_login_required
from functools import wraps

def login_required_bypass(view_func):
    """Login required decorator with development bypass"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if getattr(settings, 'DEVELOPMENT_BYPASS_AUTH', False):
            # Bypass authentication in development
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                from core.models import User
                try:
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        request.user = admin_user
                except:
                    pass
            return view_func(request, *args, **kwargs)
        else:
            # Use normal login_required in production
            return django_login_required(view_func)(request, *args, **kwargs)
    return wrapped_view


from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required as django_login_required


def permission_required_redirect(permission_list, redirect_to='dashboard', message=None):
    """
    Decorator that redirects users to a specific page if they don't have required permissions.
    Instead of showing 403 Forbidden, redirects with a friendly message.
    
    Args:
        permission_list: List of permissions required (user needs ALL permissions)
        redirect_to: URL name to redirect to (default: 'dashboard')
        message: Custom message to show (default: generic message)
    """
    def decorator(view_func):
        @wraps(view_func)
        @django_login_required
        def wrapper(request, *args, **kwargs):
            # Check if user has all required permissions
            has_all_permissions = True
            if isinstance(permission_list, str):
                has_all_permissions = request.user.has_perm(permission_list)
            else:
                for permission in permission_list:
                    if not request.user.has_perm(permission):
                        has_all_permissions = False
                        break
            
            if not has_all_permissions:
                if message:
                    messages.error(request, message)
                else:
                    messages.error(request, 'You do not have permission to access this page.')
                return redirect(redirect_to)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def superuser_required_redirect(redirect_to='dashboard', message=None):
    """Decorator for views that require superuser permissions"""
    return permission_required_redirect(
        'core.can_manage_system', 
        redirect_to=redirect_to,
        message=message or 'This page is only available to system administrators.'
    )


def staff_or_superuser_required_redirect(redirect_to='dashboard', message=None):
    """Decorator for views that require staff-level permissions"""
    return permission_required_redirect(
        'core.can_modify_users',
        redirect_to=redirect_to,
        message=message or 'This page requires administrative privileges.'
    )