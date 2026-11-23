from django.utils.crypto import salted_hmac

from .models import OfficerApplication, User, UserRole


def user_data(user):
    roles = list(UserRole.objects.filter(user=user).order_by('role__code').values_list('role__code', flat=True))
    officer_status = (OfficerApplication.objects.filter(user=user).order_by('-created_at', '-id')
                      .values_list('status', flat=True).first())
    return {
        'id': str(user.pk),
        'username': user.username,
        'email': user.email,
        'fullName': user.full_name,
        'roles': roles,
        'officerStatus': officer_status,
    }


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


def authenticate_user(identifier, password):
    identifier = identifier.strip()
    if '@' in identifier:
        user = User.objects.filter(email__iexact=identifier).first()
    else:
        user = User.objects.filter(username__iexact=identifier).first()
    if user is None or not user.is_active or not user.check_password(password):
        return None
    return user
