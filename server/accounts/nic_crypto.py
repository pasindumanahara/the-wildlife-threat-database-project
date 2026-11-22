"""Authenticated encryption for NIC values stored in users.nic_encrypted."""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class NICCipher:
    PREFIX = 'fernet:'

    def __init__(self, key=None):
        key = key or settings.NIC_ENCRYPTION_KEY
        if not key:
            raise ImproperlyConfigured('Set NIC_ENCRYPTION_KEY in server/.env before saving NICs.')
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except (TypeError, ValueError) as exc:
            raise ImproperlyConfigured('NIC_ENCRYPTION_KEY must be a Fernet key.') from exc

    def encrypt(self, plaintext):
        if not plaintext:
            return None
        return self.PREFIX + self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, value):
        if not value:
            return None
        if not value.startswith(self.PREFIX):
            raise ValueError('NIC value has not been encrypted.')
        try:
            return self._fernet.decrypt(value[len(self.PREFIX):].encode()).decode()
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise ValueError('NIC value cannot be decrypted.') from exc
