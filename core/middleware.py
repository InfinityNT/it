from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
import re


class HTMXContentMiddleware(MiddlewareMixin):
    """
    Middleware to automatically handle HTMX requests and content-only responses.
    """

    TEMPLATE_MAPPING = {
        # Core templates
        'core/dashboard.html': 'pages/dashboard.html',
        'core/users.html': 'pages/user-list.html',
        'core/user_list.html': 'pages/user-list.html',
        'core/user_detail.html': 'pages/user-detail.html',
        'core/add_user.html': 'forms/user-create.html',
        'core/user_edit.html': 'forms/user-edit.html',
        'core/profile_settings.html': 'forms/profile-edit.html',
        'core/password_change.html': 'forms/password-change.html',
        'core/login.html': 'forms/login.html',

        # Device templates
        'devices/devices.html': 'pages/device-list.html',
        'devices/device_list.html': 'pages/device-list.html',
        'devices/device_detail.html': 'pages/device-detail.html',
        'devices/add_device.html': 'forms/device-create.html',
        'devices/edit_device.html': 'forms/device-edit.html',
        'devices/advanced_search.html': 'pages/advanced-search.html',
        'devices/device_history.html': 'pages/device-history.html',

        # Assignment templates
        'assignments/assignments.html': 'pages/assignment-list.html',
        'assignments/assignment_list.html': 'pages/assignment-list.html',
        'assignments/assignment_detail.html': 'pages/assignment-detail.html',
        'assignments/assign_device.html': 'forms/assignment-create.html',
        'assignments/return_device.html': 'forms/device-return.html',
        'assignments/employee_assignment_list.html': 'pages/employee-assignments.html',

        # Approval templates
        'approvals/approvals.html': 'pages/approval-list.html',
        'approvals/approval_list.html': 'pages/approval-list.html',

        # Employee templates
        'employees/employees.html': 'pages/employee-list.html',
        'employees/employee_detail.html': 'pages/employee-detail.html',
        'employees/add_employee.html': 'forms/employee-create.html',
        'employees/employee_edit.html': 'forms/employee-edit.html',

        # Report templates
        'reports/reports.html': 'pages/reports.html',
        'reports/custom_report_form.html': 'forms/report-create.html',

        # Docs templates
        'docs/docs.html': 'docs/docs_content.html',
        'docs/docs_page.html': 'docs/docs_page_content.html',
    }

    def process_request(self, request):
        """Add HTMX detection flags to the request."""
        request.is_htmx = request.headers.get('HX-Request') == 'true'
        request.is_htmx_boosted = request.headers.get('HX-Boosted') == 'true'
        request.htmx_current_url = request.headers.get('HX-Current-URL')
        request.htmx_target = request.headers.get('HX-Target')

        # Store original template selection for views
        request.htmx_template_override = None

        return None

    def process_response(self, request, response):
        """
        Handle HTMX authentication redirects.
        When an HTMX request hits a @login_required view while unauthenticated,
        Django returns a 302 redirect to login. We intercept this and return
        an HX-Redirect header so HTMX does a full page redirect instead of
        loading the login page inside the content area.
        """
        if request.is_htmx and response.status_code == 302:
            redirect_url = response.get('Location', '')
            # Check if redirecting to login page
            if '/login/' in redirect_url:
                response['HX-Redirect'] = redirect_url
                response.status_code = 200

        return response
    
    def process_template_response(self, request, response):
        """
        Automatically switch to content-only templates for HTMX requests.
        """
        if hasattr(response, 'template_name') and request.is_htmx:
            template_name = response.template_name
            
            # Handle both string and list template names
            if isinstance(template_name, list):
                template_name = template_name[0]
            
            # Skip processing if template_name is None (e.g., for JSON responses)
            if template_name is None:
                return response
            
            # Convert full page templates to content-only templates
            content_template = self.get_content_template(template_name)
            if content_template:
                response.template_name = content_template
        
        return response
    
    def get_content_template(self, template_name):
        """
        Convert a full page template name to its content-only equivalent.
        """
        # Direct mapping
        if template_name in self.TEMPLATE_MAPPING:
            return self.TEMPLATE_MAPPING[template_name]
        
        # Content-only templates (already converted)
        if template_name.startswith('pages/') or template_name.startswith('forms/') or \
           template_name.startswith('partials/') or template_name.startswith('modals/'):
            return template_name
        
        # Try to convert _content.html templates
        if template_name.endswith('_content.html'):
            base_name = template_name.replace('_content.html', '')
            if base_name in self.TEMPLATE_MAPPING:
                return self.TEMPLATE_MAPPING[base_name]
        
        # If no mapping found, return None to use original template
        return None


class PasswordChangeRequiredMiddleware:
    """Middleware to force password change for users who need it"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that should be allowed even when password change is required
        self.allowed_urls = [
            '/accounts/password/change/',
            '/accounts/logout/',
            '/admin/password_change/',
            '/password-change/',
            '/api/',  # Allow all API endpoints
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Skip middleware for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip middleware for superusers
        if request.user.is_superuser:
            return self.get_response(request)
            
        # Skip middleware for allowed URLs
        if any(request.path.startswith(url) for url in self.allowed_urls):
            return self.get_response(request)
        
        # Check if user needs to change password
        if hasattr(request.user, 'needs_password_change') and request.user.needs_password_change:
            # Add message to inform user
            messages.warning(request, 'You must change your password before continuing.')
            return redirect('password-change')

        return self.get_response(request)


class SessionTimeoutMiddleware:
    """Middleware to enforce session timeout based on SystemSettings"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            '/login/',
            '/logout/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if any(request.path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)

        # Get session timeout from settings
        try:
            from core.models import SystemSettings
            timeout_setting = SystemSettings.objects.filter(
                key='session_timeout', is_active=True
            ).first()
            timeout_minutes = int(timeout_setting.value) if timeout_setting else 30
        except (ValueError, Exception):
            timeout_minutes = 30

        if timeout_minutes > 0:
            last_activity = request.session.get('last_activity')
            now = timezone.now().timestamp()

            if last_activity:
                elapsed = (now - last_activity) / 60  # minutes
                if elapsed > timeout_minutes:
                    logout(request)
                    messages.warning(request, 'Your session has expired due to inactivity. Please log in again.')
                    return redirect('login')

            # Update last activity
            request.session['last_activity'] = now

        return self.get_response(request)


class TimezoneMiddleware:
    """Middleware to activate the timezone configured in SystemSettings"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from core.models import SystemSettings
            import zoneinfo
            tz_setting = SystemSettings.objects.filter(
                key='timezone', is_active=True
            ).first()
            if tz_setting and tz_setting.value:
                timezone.activate(zoneinfo.ZoneInfo(tz_setting.value))
            else:
                timezone.deactivate()
        except Exception:
            timezone.deactivate()

        return self.get_response(request)


class PasswordExpiryMiddleware:
    """Middleware to enforce password expiry based on SystemSettings"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            '/login/',
            '/logout/',
            '/password-change/',
            '/static/',
            '/media/',
            '/api/',
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_superuser:
            return self.get_response(request)

        if any(request.path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)

        # Get password expiry from settings
        try:
            from core.models import SystemSettings
            expiry_setting = SystemSettings.objects.filter(
                key='password_expiry', is_active=True
            ).first()
            expiry_days = int(expiry_setting.value) if expiry_setting else 90
        except (ValueError, Exception):
            expiry_days = 90

        if expiry_days > 0 and hasattr(request.user, 'password_changed_at'):
            password_changed = request.user.password_changed_at
            if password_changed:
                from datetime import timedelta
                expiry_date = password_changed + timedelta(days=expiry_days)
                if timezone.now() > expiry_date:
                    messages.warning(request, 'Your password has expired. Please change it to continue.')
                    return redirect('password-change')

        return self.get_response(request)