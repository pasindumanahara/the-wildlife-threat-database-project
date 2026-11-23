import json
import tempfile
from io import BytesIO

from PIL import Image
from cryptography.fernet import Fernet
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase, override_settings

from .models import (Address, MediaAsset, OfficerApplication, User, UserRole,
                     validate_nic, validate_office_phone, validate_signup_email,
                     validate_signup_password)
from .nic_crypto import NICCipher
from .views import validate_upload


@override_settings(NIC_ENCRYPTION_KEY=Fernet.generate_key().decode())
class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.details = {
            'fullName': 'Wildlife Tester',
            'username': 'wildlife_tester',
            'email': 'tester@example.com',
            'password': 'A-strong-test-password-123',
            'nic': '123456789V',
            'mobile': '771234567',
            'AddressLine1': '1 Main Road',
            'City': 'Colombo',
            'PostalCode': '00100',
        }

    def post(self, path, details, token=None):
        return self.client.post(
            path,
            data=json.dumps(details),
            content_type='application/json',
            headers={'X-CSRFToken': token} if token else {},
        )

    def token(self):
        return self.client.get('/api/auth/csrf/').json()['csrfToken']

    def test_session_flow_and_csrf(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.assertEqual(self.post('/api/auth/register/', self.details).status_code, 403)
        self.assertEqual(self.post('/api/auth/register/', self.details, self.token()).status_code, 201)
        user = User.objects.get(username='wildlife_tester')
        self.assertTrue(user.check_password(self.details['password']))
        self.assertEqual(UserRole.objects.get(user=user).role.code, 'user')
        self.assertEqual(self.client.get('/api/auth/me/').json()['user']['id'], str(user.pk))
        self.assertEqual(self.post('/api/auth/logout/', {}, self.token()).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.assertEqual(self.post('/api/auth/login/', {
            'identifier': 'TESTER@EXAMPLE.COM', 'password': self.details['password']
        }, self.token()).status_code, 200)

    def test_invalid_credentials_and_incomplete_officer(self):
        self.assertEqual(self.post('/api/auth/register/', {
            **self.details, 'account': 'officer'
        }, self.token()).status_code, 400)
        self.assertEqual(self.post('/api/auth/register/', self.details, self.token()).status_code, 201)
        self.assertEqual(self.post('/api/auth/logout/', {}, self.token()).status_code, 200)
        self.assertEqual(self.post('/api/auth/login/', {
            'identifier': self.details['username'], 'password': 'wrong'
        }, self.token()).status_code, 400)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_full_officer_signup_saves_profile_and_pending_application(self):
        image_bytes = BytesIO()
        Image.new('RGB', (100, 100), 'green').save(image_bytes, format='PNG')
        details = {
            **self.details,
            'account': 'officer',
            'nic': '123456789V',
            'mobile': '771234567',
            'countryCode': 'LK',
            'AddressLine1': '1 Main Road',
            'City': 'Colombo',
            'PostalCode': '00100',
            'workAddressLine1': '2 Office Road',
            'workCity': 'Kandy',
            'workPostalCode': '20000',
            'designation': 'Wildlife officer',
            'officePhone': '0111234567',
            'photo': SimpleUploadedFile('photo.png', image_bytes.getvalue(), content_type='image/png'),
            'document': SimpleUploadedFile('proof.pdf', b'%PDF-1.4\nverification', content_type='application/pdf'),
        }
        with tempfile.TemporaryDirectory() as uploads, override_settings(MEDIA_ROOT=uploads):
            response = self.client.post('/api/auth/register/', data=details, headers={'X-CSRFToken': self.token()})
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(response.json()['officerStatus'], 'pending')
            user = User.objects.get(username=self.details['username'])
            self.assertTrue(user.nic.startswith('fernet:'))
            self.assertNotIn('123456789V', user.nic)
            self.assertEqual(user.get_nic(), '123456789V')
            photo = MediaAsset.objects.get(owner_user=user, status='profile_photo')
            self.assertTrue(photo.storage_key.startswith('profiles/'))
            self.assertEqual(Address.objects.filter(user=user).count(), 2)
            application = OfficerApplication.objects.get(user=user)
            self.assertEqual(application.status, 'pending')
            # self.assertEqual(application.verification_media.status, 'verification')
            self.assertEqual(UserRole.objects.get(user=user).role.code, 'user')

    def test_multipart_signup_without_photo(self):
        details = {
            **self.details,
            'account': 'regular',
            'nic': '123456789V',
            'mobile': '771234567',
            'countryCode': 'LK',
            'AddressLine1': '1 Main Road',
            'City': 'Colombo',
            'PostalCode': '00100',
        }
        response = self.client.post('/api/auth/register/', data=details, headers={'X-CSRFToken': self.token()})
        self.assertEqual(response.status_code, 201, response.content)
        user = User.objects.get(username=self.details['username'])
        self.assertEqual(user.get_nic(), '123456789V')
        self.assertFalse(MediaAsset.objects.filter(owner_user=user).exists())
        self.assertEqual(Address.objects.filter(user=user).count(), 1)

    def test_password_policy_rejects_weak_password(self):
        details = {**self.details, 'username': 'password', 'password': 'password'}
        response = self.post('/api/auth/register/', details, self.token())
        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(User.objects.filter(username='password').exists())

    def test_signup_rejects_invalid_required_fields(self):
        for field, value in (
            ('nic', ''),
            ('nic', '120007890V'),
            ('mobile', ''),
            ('AddressLine1', ''),
            ('email', 'tester..name@example.com'),
        ):
            with self.subTest(field=field, value=value):
                response = self.post('/api/auth/register/', {
                    **self.details, field: value,
                }, self.token())
                self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(User.objects.exists())

    def test_nic_cipher_is_randomized_and_rejects_wrong_key(self):
        value = NICCipher().encrypt('123456789V')
        self.assertNotEqual(value, NICCipher().encrypt('123456789V'))
        with self.assertRaises(ValueError):
            NICCipher(Fernet.generate_key()).decrypt(value)


class SignupValidationTests(SimpleTestCase):
    def test_signup_validators_match_form_rules(self):
        self.assertEqual(validate_nic(' 123456789v '), '123456789V')
        self.assertEqual(validate_signup_email(' Tester@Example.com '), 'tester@example.com')
        self.assertEqual(validate_office_phone('(+94) 11-2345678'), '+94112345678')
        self.assertEqual(validate_signup_password('Strong-Password123'), 'Strong-Password123')
        for validator, value in (
            (validate_nic, '1234567890V'),
            (validate_nic, '189900112345'),
            (validate_nic, '120007890V'),
            (validate_signup_email, 'test..name@example.com'),
            (validate_signup_password, 'Password 123!'),
            (validate_office_phone, '+940123456789'),
        ):
            with self.subTest(validator=validator.__name__, value=value):
                with self.assertRaises(ValidationError):
                    validator(value)

    def test_upload_validation_rejects_disguised_files(self):
        for name, content, content_type, kind in (
            ('proof.exe.pdf', b'%PDF-1.4\n', 'application/pdf', 'document'),
            ('proof.pdf', b'not a pdf', 'application/pdf', 'document'),
            ('proof.pdf', b'%PDF-1.4\n', 'text/plain', 'document'),
            ('photo.png', b'%PDF-1.4\n', 'image/png', 'photo'),
        ):
            with self.subTest(name=name, content_type=content_type, kind=kind):
                file = SimpleUploadedFile(name, content, content_type=content_type)
                with self.assertRaises(ValidationError):
                    validate_upload(file, kind)

        small_image = BytesIO()
        Image.new('RGB', (99, 100), 'green').save(small_image, format='PNG')
        file = SimpleUploadedFile('photo.png', small_image.getvalue(), content_type='image/png')
        with self.assertRaises(ValidationError):
            validate_upload(file, 'photo')
