from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CustomPasswordValidator:
    """
    Custom password validator that keeps the password policy user-friendly
    while still blocking obviously weak choices.
    """

    def validate(self, password, user=None):
        errors = []

        # Check for common patterns that should be avoided
        if password.lower() in ['password', '123456', 'qwerty', 'admin', 'user', 'kiraya']:
            errors.append(_("This password is too common. Please choose a more unique password."))

        # Check for long sequential character runs such as abc or 123.
        for i in range(len(password) - 2):
            if (ord(password[i]) + 1 == ord(password[i + 1]) and
                ord(password[i + 1]) + 1 == ord(password[i + 2])):
                errors.append(_("Password should not contain sequential characters."))
                break

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password should be at least 8 characters long and should not be too common or too easy to guess."
        )
