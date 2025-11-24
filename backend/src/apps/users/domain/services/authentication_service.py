from typing import Optional
from apps.users.domain.value_objects.email import Email
from apps.users.domain.value_objects.password import Password


class AuthenticationException(Exception):
    """Исключение при ошибке аутентификации"""
    pass


class AuthenticationService:
    """
    Domain Service для аутентификации.
    """

    def authenticate(self, email: Email, password_plain: str):
        """
        Аутентифицировать пользователя.
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Ищем пользователя по email
        try:
            user = User.objects.get(email=email.value)
        except User.DoesNotExist:
            raise AuthenticationException("Неверный email или пароль")

        # Проверяем пароль
        if not user.check_password(password_plain):
            raise AuthenticationException("Неверный email или пароль")

        # Проверяем активен ли пользователь
        if not user.is_active:
            raise AuthenticationException("Аккаунт заблокирован")

        return user

    def is_password_correct(self, user, password_plain: str) -> bool:
        """
        Проверить правильность пароля для пользователя.
        """
        return user.check_password(password_plain)

