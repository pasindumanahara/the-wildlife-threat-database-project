import uuid

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import MediaAsset


DANGEROUS_EXTENSIONS = {
    'exe', 'bat', 'cmd', 'sh', 'msi', 'dll', 'scr', 'pif', 'com', 'js', 'mjs', 'cjs',
    'jsx', 'ts', 'vbs', 'ps1', 'php', 'phtml', 'py', 'rb', 'pl', 'jsp', 'asp', 'aspx',
    'html', 'htm', 'svg', 'xml', 'jar', 'war', 'hta', 'zip', 'rar', '7z', 'tar', 'gz',
}
IMAGE_TYPES = {'jpg': ('JPEG', 'image/jpeg'), 'jpeg': ('JPEG', 'image/jpeg'),
               'png': ('PNG', 'image/png'), 'webp': ('WEBP', 'image/webp')}


def validate_upload(file, kind):
    if file.size == 0:
        raise ValidationError('The selected file is empty.')
    if '/' in file.name or '\\' in file.name or '\0' in file.name or '..' in file.name:
        raise ValidationError('Invalid or suspicious file name.')
    parts = file.name.lower().split('.')
    if len(parts) < 2 or any(part in DANGEROUS_EXTENSIONS for part in parts[1:-1]):
        raise ValidationError('Invalid or suspicious file name.')
    extension = parts[-1]
    if kind == 'photo':
        if file.size > 2 * 1024 * 1024:
            raise ValidationError('Profile photo must be under 2 MB.')
        if extension not in IMAGE_TYPES or file.content_type != IMAGE_TYPES[extension][1]:
            raise ValidationError('Choose a valid JPEG, PNG, or WebP image.')
        try:
            image = Image.open(file)
            image_format = image.format
            width, height = image.size
            image.verify()
            if image_format != IMAGE_TYPES[extension][0]:
                raise ValidationError('Image content does not match its extension.')
            if not (100 <= width <= 4096 and 100 <= height <= 4096):
                raise ValidationError('Image dimensions must be between 100x100 and 4096x4096 pixels.')
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
            raise ValidationError('Choose a valid JPEG, PNG, or WebP image.')
        finally:
            file.seek(0)
        file.name = uuid.uuid4().hex + '.' + extension
    else:
        if file.size > 10 * 1024 * 1024 or extension != 'pdf' or file.content_type != 'application/pdf':
            raise ValidationError('Choose a PDF document under 10 MB.')
        file.seek(0)
        if file.read(5) != b'%PDF-':
            raise ValidationError('Choose a PDF document under 10 MB.')
        file.seek(0)
        file.name = uuid.uuid4().hex + '.pdf'


def save_profile_photo(user, photo, photo_name, saved_files):
    path = default_storage.save('profiles/' + photo.name, photo)
    saved_files.append(path)
    MediaAsset.objects.create(owner_user=user, storage_key=path,
                              original_filename=photo_name, mime_type=photo.content_type,
                              file_size=photo.size, status='profile_photo', uploaded_at=timezone.now())


def save_officer_document(user, document, document_name, saved_files):
    path = default_storage.save('officer_documents/' + document.name, document)
    saved_files.append(path)
    asset = MediaAsset.objects.create(owner_user=user, storage_key=path,
                                      original_filename=document_name, mime_type='application/pdf',
                                      file_size=document.size, status='verification', uploaded_at=timezone.now())
    return asset


def delete_saved_files(saved_files):
    for path in saved_files:
        default_storage.delete(path)
