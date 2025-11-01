from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
import re


class HTMXContentMiddleware(MiddlewareMixin):
    """
    Middleware to automatically handle HTMX requests and content-only responses.
    """

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
        # Mapping of old templates to new semantic templates
        template_mapping = {
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
        }
        
        # Direct mapping
        if template_name in template_mapping:
            return template_mapping[template_name]
        
        # Content-only templates (already converted)
        if template_name.startswith('pages/') or template_name.startswith('forms/') or \
           template_name.startswith('partials/') or template_name.startswith('modals/'):
            return template_name
        
        # Try to convert _content.html templates
        if template_name.endswith('_content.html'):
            base_name = template_name.replace('_content.html', '')
            if base_name in template_mapping:
                return template_mapping[base_name]
        
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