
from django.contrib.auth.password_validation import validate_password as django_validate_password

from django.core.exceptions import ValidationError

def validate_password(value):
    try:
        # Use Django's built-in password validation
        django_validate_password(value)
    except ValidationError as e:
        # Return the error message
        return " ".join(e.messages)
    return None  # Return None if there are no errors
