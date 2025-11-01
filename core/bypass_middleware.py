"""
Development-only middleware to bypass authentication for testing
"""
from django.conf import settings

class DevelopmentAuthBypassMiddleware:
    """Bypass authentication for development testing"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add fake authenticated user for development
        if getattr(settings, 'DEVELOPMENT_BYPASS_AUTH', False):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                from core.models import User
                try:
                    # Use admin user or create a fake one
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        request.user = admin_user
                        request._cached_user = admin_user
                except:
                    pass
        
        response = self.get_response(request)
        return response
