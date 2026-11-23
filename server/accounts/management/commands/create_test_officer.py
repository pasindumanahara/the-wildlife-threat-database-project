"""Create a synthetic approved officer account for local development."""

import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import OfficerApplication, Role, User, UserRole
from accounts.validators import text_field, validate_signup_email, validate_signup_password


def generate_password():
    symbols = '!@#$%&*'
    alphabet = string.ascii_letters + string.digits + symbols
    characters = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(symbols),
    ]
    characters.extend(secrets.choice(alphabet) for _ in range(16))
    secrets.SystemRandom().shuffle(characters)
    return ''.join(characters)


class Command(BaseCommand):
    help = 'Create a synthetic approved officer account for local development only.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='test_officer')
        parser.add_argument('--email', default='test.officer@example.test')
        parser.add_argument('--full-name', default='Test Officer')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('This command is available only when DJANGO_DEBUG=true.')

        try:
            username = text_field(options, 'username', 50, True)
            email = validate_signup_email(options['email'])
            full_name = text_field({'fullName': options['full_name']}, 'fullName', 150, True)
            User._meta.get_field('username').run_validators(username)
            User._meta.get_field('email').run_validators(email)
            User._meta.get_field('full_name').run_validators(full_name)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from error

        if User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            raise CommandError('Username or email is already in use; no account was changed.')

        try:
            regular_role = Role.objects.get(code='user')
            officer_role = Role.objects.get(code='officer')
        except Role.DoesNotExist as error:
            raise CommandError('Required roles are missing. Run database migrations first.') from error

        password = validate_signup_password(generate_password())
        try:
            with transaction.atomic():
                user = User(username=username, email=email, full_name=full_name)
                user.set_password(password)
                user.save()
                UserRole.objects.create(user=user, role=regular_role)
                UserRole.objects.create(user=user, role=officer_role)
                OfficerApplication.objects.create(
                    user=user,
                    designation='Wildlife officer',
                    status='approved',
                    reviewed_at=timezone.now(),
                    review_note='Synthetic account for local development.',
                )
        except IntegrityError as error:
            raise CommandError('Username or email is already in use; no account was changed.') from error

        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write('Officer status: approved')
