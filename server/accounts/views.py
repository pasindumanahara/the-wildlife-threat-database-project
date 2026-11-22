import json
import uuid

from PIL import Image, UnidentifiedImageError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .models import Address, MediaAsset, OfficerApplication, Role, User, UserRole


def read_json(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def user_data(user):
    return {'id': str(user.pk), 'username': user.username, 'email': user.email, 'fullName': user.full_name}


def session_user(request):
    user_id = request.session.get('wildlife_user_id')
    if not user_id:
        return None
    user = User.objects.filter(id=user_id, is_active=True).first()
    expected = salted_hmac('wildlife.session', user.password).hexdigest() if user else None
    if not user or request.session.get('wildlife_auth_hash') != expected:
        request.session.flush()
        return None
    return user


def start_session(request, user):
    request.session.cycle_key()
    request.session['wildlife_user_id'] = str(user.pk)
    request.session['wildlife_auth_hash'] = salted_hmac('wildlife.session', user.password).hexdigest()


def text_field(data, name, limit, required=False):
    value = data.get(name, '')
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise ValidationError(f'Enter a valid {name}.')
    return value.strip()


def address_fields(data, prefix):
    keys = ('AddressLine1', 'AddressLine2', 'AddressLine3', 'City', 'Province', 'PostalCode')
    if not any(data.get(prefix + key) for key in keys):
        return None
    return {
        'address_line_1': text_field(data, prefix + 'AddressLine1', 255, True),
        'address_line_2': text_field(data, prefix + 'AddressLine2', 255),
        'address_line_3': text_field(data, prefix + 'AddressLine3', 255),
        'city': text_field(data, prefix + 'City', 100, True),
        'province': text_field(data, prefix + 'Province', 100) or 'Western Province',
        'postal_code': text_field(data, prefix + 'PostalCode', 20, True),
    }

# TODO :: image uploading and validation
def validate_upload(file, kind):
    if kind == 'photo':
        if file.size > 5 * 1024 * 1024:
            raise ValidationError('Profile photo must be under 5 MB.')
        try:
            image = Image.open(file)
            if image.width * image.height > 20_000_000:
                raise ValidationError('Profile photo dimensions are too large.')
            image.verify()
            image_format = image.format
        except (UnidentifiedImageError, OSError, ValueError):
            raise ValidationError('Choose a valid JPEG, PNG, or WebP image.')
        finally:
            file.seek(0)
        extensions = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
        if image_format not in extensions:
            raise ValidationError('Choose a JPEG, PNG, or WebP image.')
        file.name = uuid.uuid4().hex + extensions[image_format]
    else:
        file.seek(0)
        if file.size > 10 * 1024 * 1024 or not file.name.lower().endswith('.pdf') or file.read(5) != b'%PDF-':
            raise ValidationError('Choose a PDF document under 10 MB.')
        file.seek(0)
        file.name = uuid.uuid4().hex + '.pdf'


@require_GET
def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})


@require_POST
@csrf_protect
def register(request):
    data = request.POST if request.content_type.startswith('multipart/form-data') else read_json(request)
    if data is None:
        return JsonResponse({'detail': 'Send JSON or multipart form data.'}, status=400)
    if data.get('account', 'regular') not in ('regular', 'officer'):
        return JsonResponse({'detail': 'Choose a valid account type.'}, status=400)
    allowed = {'account', 'fullName', 'username', 'email', 'password', 'nic', 'mobile', 'countryCode',
               'designation', 'officePhone'}
    allowed.update(f'{prefix}{field}' for prefix in ('', 'work')
                   for field in ('AddressLine1', 'AddressLine2', 'AddressLine3', 'City', 'Province', 'PostalCode'))
    if set(data) - allowed or set(request.FILES) - {'photo', 'document'}:
        return JsonResponse({'detail': 'The form contains unsupported fields.'}, status=400)
    officer = data.get('account') == 'officer'
    photo = request.FILES.get('photo')
    document = request.FILES.get('document')
    photo_name = photo.name[:255] if photo else None
    document_name = document.name[:255] if document else None
    try:
        username = text_field(data, 'username', 50, True)
        email = text_field(data, 'email', 320, True).lower()
        full_name = text_field(data, 'fullName', 150, True)
        password = text_field(data, 'password', 128, True)
        nic = text_field(data, 'nic', 30)
        mobile = text_field(data, 'mobile', 20)
        country_code = text_field(data, 'countryCode', 2) or 'LK'
        if len(country_code) != 2 or not country_code.isalpha():
            raise ValidationError('Choose a valid country code.')
        personal_address = address_fields(data, '')
        work_address = address_fields(data, 'work') if officer else None
        designation = text_field(data, 'designation', 100, officer)
        office_phone = text_field(data, 'officePhone', 20, officer)
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
    except ValidationError as error:
        return JsonResponse({'detail': ' '.join(error.messages)}, status=400)

    if User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'detail': 'Username or email is already in use.'}, status=400)
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
                path = default_storage.save('profiles/' + photo.name, photo)
                saved_files.append(path)
                MediaAsset.objects.create(owner_user=user, storage_key=path,
                                          original_filename=photo_name, mime_type=photo.content_type,
                                          file_size=photo.size, status='profile_photo', uploaded_at=timezone.now())
            if officer:
                path = default_storage.save('officer_documents/' + document.name, document)
                saved_files.append(path)
                asset = MediaAsset.objects.create(owner_user=user, storage_key=path,
                                                  original_filename=document_name, mime_type='application/pdf',
                                                  file_size=document.size, status='verification', uploaded_at=timezone.now())
                OfficerApplication.objects.create(user=user, designation=designation,
                                                  office_phone=office_phone, verification_media=asset)
    except IntegrityError:
        for path in saved_files:
            default_storage.delete(path)
        return JsonResponse({'detail': 'Username or email is already in use.'}, status=400)
    except Exception:
        for path in saved_files:
            default_storage.delete(path)
        raise
    start_session(request, user)
    return JsonResponse({'user': user_data(user), 'officerStatus': 'pending' if officer else None}, status=201)


@require_POST
@csrf_protect
def sign_in(request):
    data = read_json(request)
    if data is None:
        return JsonResponse({'detail': 'Send a JSON object.'}, status=400)
    identifier = data.get('identifier')
    password = data.get('password')
    if not isinstance(identifier, str) or not identifier.strip() or not isinstance(password, str) or not password:
        return JsonResponse({'detail': 'Enter your username or email and password.'}, status=400)
    identifier = identifier.strip()
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
    else:
        user = User.objects.filter(username__iexact=identifier).first()
    if user is None or not user.is_active or not user.check_password(password):
        return JsonResponse({'detail': 'Invalid username/email or password.'}, status=400)
    start_session(request, user)
    return JsonResponse({'user': user_data(user)})


@require_POST
@csrf_protect
def sign_out(request):
    request.session.flush()
    return JsonResponse({'detail': 'Signed out.'})


@require_GET
def me(request):
    user = session_user(request)
    if user is None:
        return JsonResponse({'detail': 'Authentication required.'}, status=401)
    return JsonResponse({'user': user_data(user)})
