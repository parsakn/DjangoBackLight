from urllib.parse import parse_qs

import jwt
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser


@sync_to_async
def _get_user_from_token(token: str):
    """
    Resolve a Django user instance from a SimpleJWT access token.
    Returns AnonymousUser on any failure.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            return AnonymousUser()
        User = get_user_model()
        return User.objects.get(pk=user_id)
    except Exception:
        return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    """
    Middleware stack that first applies Django's session-based AuthMiddlewareStack
    and then, if a ?token=<JWT> query parameter is present, overrides `scope["user"]`
    with the user resolved from that JWT.
    """

    base_app = AuthMiddlewareStack(inner)

    async def app(scope, receive, send):
        scope = dict(scope)

        # Existing user from session/cookie auth
        user = scope.get("user", AnonymousUser())

        # Try to override with JWT if provided
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if token:
            user = await _get_user_from_token(token)

        scope["user"] = user
        return await base_app(scope, receive, send)

    return app

