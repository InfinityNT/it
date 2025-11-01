"""
Context processors for making data available to all templates
"""
from core.models import SystemSettings


def system_settings(request):
    """
    Add system settings to all template contexts
    """
    settings_dict = {}

    try:
        # Load all active system settings
        settings_queryset = SystemSettings.objects.filter(is_active=True)
        for setting in settings_queryset:
            settings_dict[setting.key] = setting.value
    except Exception:
        # If database isn't set up yet or other error, use defaults
        pass

    # Set defaults for important settings
    system_name = settings_dict.get('system_name', 'IT Device Management')
    admin_email = settings_dict.get('admin_email', 'admin@company.com')

    return {
        'SYSTEM_NAME': system_name,
        'ADMIN_EMAIL': admin_email,
        'system_settings': settings_dict,
    }
