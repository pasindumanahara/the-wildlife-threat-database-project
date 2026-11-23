import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .authentication import authenticate_user, session_user, start_session, user_data
from .registration import create_account


def read_json(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


@require_GET
def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})


@require_POST
@csrf_protect
def register(request):
    data = request.POST if request.content_type.startswith('multipart/form-data') else read_json(request)
    if data is None:
        return JsonResponse({'detail': 'Send JSON or multipart form data.'}, status=400)
    try:
        user, officer = create_account(data, request.FILES)
    except ValidationError as error:
        return JsonResponse({'detail': ' '.join(error.messages)}, status=400)
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
    user = authenticate_user(identifier, password)
    if user is None:
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
