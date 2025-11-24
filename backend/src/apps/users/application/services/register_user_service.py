from django.db import transaction
from django.contrib.auth import get_user_model

from apps.users.domain.value_objects.email import Email
from apps.users.domain.value_objects.password import Password


class RegistrationException(Exception):
    """Исключение при ошибке регистрации"""
    pass


class RegisterUserService:
    """
    Application Service для регистрации пользователя.
    """

    @transaction.atomic
    def execute(
        self,
        email: str,
        password: str,
        nickname: str = None
    ):
        """
        Зарегистрировать нового пользователя.
        """
        User = get_user_model()

        # 1. Валидация через Value Objects
        try:
            email_vo = Email(email)
        except ValueError as e:
            raise RegistrationException(f"Некорректный email: {e}")

        try:
            password_vo = Password.create(password)
        except ValueError as e:
            raise RegistrationException(f"Некорректный пароль: {e}")

        # 2. Проверка уникальности email
        if User.objects.filter(email=email_vo.value).exists():
            raise RegistrationException("Пользователь с таким email уже существует")

        # 3. Генерация никнейма если не указан
        if not nickname:
            nickname = self._generate_nickname(email_vo)

        # 4. Создание пользователя
        user = User.objects.create_user(
            email=email_vo.value,
            password=password,
            nickname=nickname
        )


        return user

    def _generate_nickname(self, email: Email) -> str:
        """
        Сгенерировать никнейм из email.
        """
        # Берём локальную часть email
        return email.local_part.capitalize()

