"""
Custom validators for authentication.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_password_strength(password: str):
    """
    Validate password meets security requirements.
    
    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
    """
    if len(password) < 8:
        raise ValidationError(_("Password must be at least 8 characters long."))
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_("Password must contain at least one uppercase letter."))
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(_("Password must contain at least one lowercase letter."))
    
    if not re.search(r'\d', password):
        raise ValidationError(_("Password must contain at least one digit."))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_("Password must contain at least one special character."))