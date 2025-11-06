import re

from django.forms import ValidationError


email_regex = re.recompile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
phone_regex = re.compile(r'^\+?1?\d{9,15}$')

def check_email_or_phone(email_or_phone):
    if email_regex.fullmatch(email_or_phone):
        email_or_phone = 'email'
    elif phone_regex.fullmatch(email_or_phone):
        email_or_phone = 'phone'
    else:
        data = {
            "success": False,
            "message": "Invalid email or phone number format."
        }
        raise ValidationError(data)
    return email_or_phone