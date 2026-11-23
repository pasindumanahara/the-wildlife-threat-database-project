import re
import uuid
from datetime import date

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .nic_crypto import NICCipher


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


# The application tables are defined by database/001_initial_schema.sql.
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=320, unique=True)
    password = models.CharField(max_length=128)
    nic = models.TextField(db_column='nic_encrypted', null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_nic(self, nic_plaintext):
        self.nic = NICCipher().encrypt(nic_plaintext) if nic_plaintext else None

    def get_nic(self):
        return NICCipher().decrypt(self.nic) if self.nic else None

    class Meta:
        managed = False
        db_table = 'users'


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255, null=True, blank=True)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    address_line_3 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=2, default='LK')

    class Meta:
        managed = False
        db_table = 'user_addresses'
        constraints = [models.UniqueConstraint(fields=['user', 'address_type'], name='user_address_type_unique')]


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'roles'


class UserRole(models.Model):
    pk = models.CompositePrimaryKey('user_id', 'role_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'user_roles'


class MediaAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_assets')
    storage_key = models.CharField(max_length=512, unique=True)
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    uploaded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'media_assets'


class OfficerApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='officer_applications')
    designation = models.CharField(max_length=100, null=True, blank=True)
    office_phone = models.CharField(max_length=20, null=True, blank=True)
    verification_media = models.ForeignKey(MediaAsset, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
    reviewed_by = models.ForeignKey(User, db_column='reviewed_by', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'officer_applications'
