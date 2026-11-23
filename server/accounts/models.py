import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from .nic_crypto import NICCipher
from .validators import (validate_nic, validate_office_phone, validate_signup_email,
                         validate_signup_password)


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
