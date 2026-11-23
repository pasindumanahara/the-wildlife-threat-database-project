from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from ..authentication import user_data
from ..models import OfficerApplication, User, UserRole


@override_settings(DEBUG=True)
class CreateTestOfficerCommandTests(TestCase):
    def test_creates_approved_officer_with_working_password(self):
        output = StringIO()
        call_command('create_test_officer', stdout=output)

        user = User.objects.get(username='test_officer')
        password = next(line.split(': ', 1)[1] for line in output.getvalue().splitlines()
                        if line.startswith('Password: '))
        self.assertTrue(user.check_password(password))
        self.assertEqual(set(UserRole.objects.filter(user=user).values_list('role__code', flat=True)),
                         {'user', 'officer'})
        self.assertEqual(OfficerApplication.objects.get(user=user).status, 'approved')
        self.assertEqual(user_data(user)['officerStatus'], 'approved')

        with self.assertRaises(CommandError):
            call_command('create_test_officer', stdout=StringIO())
        self.assertEqual(User.objects.count(), 1)

    @override_settings(DEBUG=False)
    def test_refuses_to_run_outside_debug_mode(self):
        with self.assertRaises(CommandError):
            call_command('create_test_officer', stdout=StringIO())
        self.assertFalse(User.objects.exists())
