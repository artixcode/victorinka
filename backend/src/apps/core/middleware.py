from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Получить пользователя из JWT токена.
    """
    from apps.users.models import User

    try:
        # Валидируем токен
        access_token = AccessToken(token_string)

        # Получаем user_id из токена
        user_id = access_token.get('user_id')

        if not user_id:
            return AnonymousUser()

        # Загружаем пользователя из БД
        user = User.objects.get(id=user_id)
        return user

    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации WebSocket соединений через JWT токен.
    """

    async def __call__(self, scope, receive, send):
        # Получаем query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)

        # Извлекаем токен
        token = query_params.get('token', [None])[0]

        if token:
            # Получаем пользователя из токена
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Обертка для применения JWTAuthMiddleware.
    """
    return JWTAuthMiddleware(inner)

