from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.domain.value_objects.email import Email
from apps.users.domain.services.authentication_service import (
    AuthenticationService,
    AuthenticationException
)


class LoginUserService:
    """
    Application Service для входа пользователя.
    """

    def __init__(self, auth_service: AuthenticationService = None):
        """
        Инициализация сервиса.
        """
        self.auth_service = auth_service or AuthenticationService()

    def execute(self, email: str, password: str) -> dict:
        """
        Выполнить вход пользователя.
        """
        # 1. Валидация email
        email_vo = Email(email)

        # 2. Аутентификация через Domain Service
        user = self.auth_service.authenticate(
            email=email_vo,
            password_plain=password
        )

        # 3. Генерация JWT токенов (инфраструктура)
        refresh = RefreshToken.for_user(user)

        # 4. Возврат токенов
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "email": user.email,
            "nickname": user.nickname
        }

