from io import BytesIO

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from ..uploads import validate_upload
from ..validators import (validate_nic, validate_office_phone, validate_signup_email,
                          validate_signup_password)


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
