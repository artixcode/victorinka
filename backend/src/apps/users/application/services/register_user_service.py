from django.db import transaction

from apps.users.domain.value_objects.email import Email
from apps.users.domain.value_objects.password import Password
from apps.users.domain.repositories import UserRepository
from apps.users.infrastructure.orm_user_repository import user_repository


class RegistrationException(Exception):
    """Исключение при ошибке регистрации"""
    pass


class RegisterUserService:
    """
    Application Service для регистрации пользователя.
    """

    def __init__(self, repository: UserRepository = None):
        """
        Инициализация сервиса с репозиторием.
        """
        self.repository = repository or user_repository

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
        if self.repository.exists_by_email(email_vo.value):
            raise RegistrationException("Пользователь с таким email уже существует")

        # 3. Генерация никнейма если не указан
        if not nickname:
            nickname = self._generate_nickname(email_vo)

        # 4. Создание пользователя
        user = self.repository.create(
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

