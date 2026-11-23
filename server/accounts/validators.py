import re
from datetime import date

from django.core.exceptions import ValidationError


def validate_nic(nic):
    if not isinstance(nic, str) or not nic.strip():
        raise ValidationError('NIC number is required.')
    nic = nic.strip().upper()
    old = re.fullmatch(r'[0-9]{2}([0-9]{3})[0-9]{4}[VX]', nic)
    new = re.fullmatch(r'([0-9]{4})([0-9]{3})[0-9]{5}', nic)
    if old:
        day = int(old.group(1))
    elif new:
        if not 1900 <= int(new.group(1)) <= date.today().year:
            raise ValidationError('NIC contains an invalid birth year.')
        day = int(new.group(2))
    else:
        raise ValidationError('Enter a valid NIC (9 digits followed by V/X, or 12 digits).')
    if not (1 <= day <= 366 or 501 <= day <= 866):
        raise ValidationError('NIC contains an invalid date code.')
    return nic


def validate_signup_email(email):
    if not isinstance(email, str) or not email.strip():
        raise ValidationError('Email address is required.')
    email = email.strip().lower()
    if len(email) > 254:
        raise ValidationError('Email address is too long.')
    if not re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email) or '..' in email:
        raise ValidationError('Enter a valid email address.')
    return email


def validate_signup_password(password):
    if not isinstance(password, str) or not password:
        raise ValidationError('Password is required.')
    if not 8 <= len(password) <= 128:
        raise ValidationError('Password must be between 8 and 128 characters long.')
    if re.search(r'\s', password):
        raise ValidationError('Password cannot contain spaces.')
    if not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password)
            and re.search(r'[0-9]', password)):
        raise ValidationError('Password must include uppercase and lowercase letters and a number.')
    if not any(char in "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?~`" for char in password):
        raise ValidationError('Password must include at least one special character.')
    return password


def validate_office_phone(phone):
    if not isinstance(phone, str) or not phone.strip():
        raise ValidationError('Office phone number is required.')
    cleaned = re.sub(r'[\s\-()]', '', phone.strip())
    if not re.fullmatch(r'(?:0|\+94|94)[1-9][0-9]{8}', cleaned):
        raise ValidationError('Enter a valid Sri Lankan office phone number.')
    return cleaned


def text_field(data, name, limit, required=False):
    value = data.get(name, '')
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise ValidationError(f'Enter a valid {name}.')
    return value.strip()


def address_fields(data, prefix, required=False):
    keys = ('AddressLine1', 'AddressLine2', 'AddressLine3', 'City', 'Province', 'PostalCode')
    if not any(data.get(prefix + key) for key in keys):
        if required:
            raise ValidationError('Complete the address.')
        return None
    return {
        'address_line_1': text_field(data, prefix + 'AddressLine1', 255, True),
        'address_line_2': text_field(data, prefix + 'AddressLine2', 255),
        'address_line_3': text_field(data, prefix + 'AddressLine3', 255),
        'city': text_field(data, prefix + 'City', 100, True),
        'province': text_field(data, prefix + 'Province', 100) or 'Western Province',
        'postal_code': text_field(data, prefix + 'PostalCode', 20, True),
    }
