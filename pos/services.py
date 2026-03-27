from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings


def auth_login(*, email: str, password: str) -> dict:
    """
    Autentica un usuario por email y password.
    Retorna un dict con access_token, token_type, expires_in y datos del usuario.
    Levanta ValidationError si las credenciales son inválidas.
    """
    user = authenticate(email=email, password=password)

    if user is None:
        raise ValidationError("Credenciales inválidas.")

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Calcular expires_in en segundos desde la configuración
    lifetime = settings.SIMPLE_JWT.get(
        'ACCESS_TOKEN_LIFETIME',
    )
    expires_in = int(lifetime.total_seconds())

    # Construir datos del rol (compatible con contrato Laravel)
    role_data = None
    if user.role is not None:
        permissions = list(
            user.role.permissions.values_list('codename', flat=True)
        )
        role_data = {
            "id": user.role.id,
            "name": user.role.name,
            "permissions": permissions,
        }

    # Construir avatar URL
    avatar_url = None
    if user.avatar and hasattr(user.avatar, 'url'):
        avatar_url = user.avatar.url

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "avatar": avatar_url,
            "role": role_data,
        },
    }
