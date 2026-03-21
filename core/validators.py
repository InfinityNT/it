import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class DynamicPasswordValidator:
    """
    Password validator that reads policy from SystemSettings.
    Supports 'standard' (8+ chars) and 'strong' (12+ chars, mixed case, numbers, symbols).
    """

    def validate(self, password, user=None):
        policy = self._get_policy()

        if policy == 'strong':
            if len(password) < 12:
                raise ValidationError(
                    _('Password must be at least 12 characters long.'),
                    code='password_too_short',
                )
            if not re.search(r'[A-Z]', password):
                raise ValidationError(
                    _('Password must contain at least one uppercase letter.'),
                    code='password_no_upper',
                )
            if not re.search(r'[a-z]', password):
                raise ValidationError(
                    _('Password must contain at least one lowercase letter.'),
                    code='password_no_lower',
                )
            if not re.search(r'[0-9]', password):
                raise ValidationError(
                    _('Password must contain at least one number.'),
                    code='password_no_number',
                )
            if not re.search(r'[^A-Za-z0-9]', password):
                raise ValidationError(
                    _('Password must contain at least one special character.'),
                    code='password_no_special',
                )
        else:
            # Standard policy: 8+ characters
            if len(password) < 8:
                raise ValidationError(
                    _('Password must be at least 8 characters long.'),
                    code='password_too_short',
                )

    def get_help_text(self):
        policy = self._get_policy()
        if policy == 'strong':
            return _(
                'Your password must be at least 12 characters long and contain '
                'uppercase letters, lowercase letters, numbers, and special characters.'
            )
        return _('Your password must be at least 8 characters long.')

    def _get_policy(self):
        try:
            from core.models import SystemSettings
            setting = SystemSettings.objects.filter(
                key='password_policy', is_active=True
            ).first()
            return setting.value if setting else 'standard'
        except Exception:
            return 'standard'
