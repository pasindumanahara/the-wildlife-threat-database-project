import json
import tempfile
from io import BytesIO

from PIL import Image
from cryptography.fernet import Fernet
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from ..models import Address, MediaAsset, OfficerApplication, Role, User, UserRole
from ..nic_crypto import NICCipher


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
        registration = self.post('/api/auth/register/', self.details, self.token())
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(registration.json()['user']['roles'], ['user'])
        self.assertIsNone(registration.json()['user']['officerStatus'])
        user = User.objects.get(username='wildlife_tester')
        self.assertTrue(user.check_password(self.details['password']))
        self.assertEqual(UserRole.objects.get(user=user).role.code, 'user')
        current_user = self.client.get('/api/auth/me/').json()['user']
        self.assertEqual(current_user['id'], str(user.pk))
        self.assertEqual(current_user['roles'], ['user'])
        self.assertIsNone(current_user['officerStatus'])
        self.assertEqual(self.post('/api/auth/logout/', {}, self.token()).status_code, 200)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        login = self.post('/api/auth/login/', {
            'identifier': 'TESTER@EXAMPLE.COM', 'password': self.details['password']
        }, self.token())
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()['user']['roles'], ['user'])
        self.assertIsNone(login.json()['user']['officerStatus'])

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
            self.assertEqual(response.json()['user']['roles'], ['user'])
            self.assertEqual(response.json()['user']['officerStatus'], 'pending')
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
            current_user = self.client.get('/api/auth/me/').json()['user']
            self.assertEqual(current_user['roles'], ['user'])
            self.assertEqual(current_user['officerStatus'], 'pending')
            self.assertEqual(self.post('/api/auth/logout/', {}, self.token()).status_code, 200)
            login = self.post('/api/auth/login/', {
                'identifier': self.details['username'], 'password': self.details['password']
            }, self.token())
            self.assertEqual(login.status_code, 200)
            self.assertEqual(login.json()['user']['roles'], ['user'])
            self.assertEqual(login.json()['user']['officerStatus'], 'pending')
            application.status = 'approved'
            application.save(update_fields=['status'])
            UserRole.objects.create(user=user, role=Role.objects.get(code='officer'))
            current_user = self.client.get('/api/auth/me/').json()['user']
            self.assertEqual(current_user['roles'], ['officer', 'user'])
            self.assertEqual(current_user['officerStatus'], 'approved')

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
