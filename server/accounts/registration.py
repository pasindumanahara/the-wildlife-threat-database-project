from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Address, OfficerApplication, Role, User, UserRole
from .uploads import delete_saved_files, save_officer_document, save_profile_photo, validate_upload
from .validators import (address_fields, text_field, validate_nic,
                         validate_office_phone, validate_signup_email,
                         validate_signup_password)


def create_account(data, files):
    # User account type validation
    if data.get('account', 'regular') not in ('regular', 'officer'):
        raise ValidationError('Choose a valid account type.')
    allowed = {'account', 'fullName', 'username', 'email', 'password', 'nic', 'mobile', 'countryCode',
               'designation', 'officePhone'}
    allowed.update(f'{prefix}{field}' for prefix in ('', 'work')
                   for field in ('AddressLine1', 'AddressLine2', 'AddressLine3', 'City', 'Province', 'PostalCode'))
    if set(data) - allowed or set(files) - {'photo', 'document'}:
        raise ValidationError('The form contains unsupported fields.')
    officer = data.get('account') == 'officer'
    photo = files.get('photo')
    document = files.get('document')
    photo_name = photo.name[:255] if photo else None
    document_name = document.name[:255] if document else None

    username = text_field(data, 'username', 50, True)
    email = validate_signup_email(data.get('email'))
    full_name = text_field(data, 'fullName', 150, True)
    password = validate_signup_password(data.get('password'))
    nic = validate_nic(data.get('nic'))
    mobile = text_field(data, 'mobile', 20, True)
    country_code = text_field(data, 'countryCode', 2) or 'LK'
    if len(country_code) != 2 or not country_code.isascii() or not country_code.isalpha():
        raise ValidationError('Choose a valid country code.')
    personal_address = address_fields(data, '', True)
    work_address = address_fields(data, 'work', True) if officer else None

    designation = text_field(data, 'designation', 100, officer)
    if officer and designation not in ('Veterinarian', 'Zoologist', 'Wildlife officer'):
        raise ValidationError('Choose a valid designation.')
    office_phone = validate_office_phone(data.get('officePhone')) if officer else ''
    if officer and (not work_address or not document):
        raise ValidationError('Complete the work address and verification document.')
    if photo:
        validate_upload(photo, 'photo')
    if document:
        if not officer:
            raise ValidationError('Verification documents are only for officer applications.')
        validate_upload(document, 'document')
    User._meta.get_field('username').run_validators(username)
    User._meta.get_field('email').run_validators(email)
    User._meta.get_field('full_name').run_validators(full_name)
    validate_password(password, user=User(username=username, email=email, full_name=full_name))

    if User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists():
        raise ValidationError('Username or email is already in use.')
    saved_files = []
    try:
        with transaction.atomic():
            user = User(username=username, email=email, full_name=full_name,
                        mobile_number=mobile or None)
            user.set_password(password)
            user.set_nic(nic or None)
            user.save()
            UserRole.objects.create(user=user, role=Role.objects.get(code='user'))
            if personal_address:
                Address.objects.create(user=user, address_type='personal',
                                       country_code=country_code, **personal_address)
            if work_address:
                Address.objects.create(user=user, address_type='work',
                                       country_code=country_code, **work_address)
            if photo:
                save_profile_photo(user, photo, photo_name, saved_files)
            if officer:
                asset = save_officer_document(user, document, document_name, saved_files)
                OfficerApplication.objects.create(user=user, designation=designation,
                                                  office_phone=office_phone, verification_media=asset)
    except IntegrityError as error:
        delete_saved_files(saved_files)
        raise ValidationError('Username or email is already in use.') from error
    except Exception:
        delete_saved_files(saved_files)
        raise
    return user, officer
