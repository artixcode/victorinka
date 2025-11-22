from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class Password:
    """
    Value Object для пароля.
    """
    hashed_value: str

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    # Требования к паролю (опционально)
    REQUIRE_DIGIT = False
    REQUIRE_UPPERCASE = False
    REQUIRE_LOWERCASE = False
    REQUIRE_SPECIAL = False

    def __post_init__(self):
        """Валидация хеша"""
        if not self.hashed_value:
            raise ValueError("Пароль не может быть пустым")

    @classmethod
    def create(cls, plain_password: str) -> 'Password':
        # Валидация
        cls._validate(plain_password)

        # Хешируем
        hashed = cls._hash_password(plain_password)

        return cls(hashed_value=hashed)

    @classmethod
    def create_hashed(cls, plain_password: str) -> 'Password':
        return cls.create(plain_password)

    @classmethod
    def from_hash(cls, hashed_password: str) -> 'Password':
        """
        Создать Password из уже захешированного значения.
        """
        return cls(hashed_value=hashed_password)

    @classmethod
    def _validate(cls, plain_password: str) -> None:
        """
        Валидация пароля.
        """
        if not plain_password:
            raise ValueError("Пароль не может быть пустым")

        if len(plain_password) < cls.MIN_LENGTH:
            raise ValueError(
                f"Пароль слишком короткий (минимум {cls.MIN_LENGTH} символов)"
            )

        if len(plain_password) > cls.MAX_LENGTH:
            raise ValueError(
                f"Пароль слишком длинный (максимум {cls.MAX_LENGTH} символов)"
            )

        # Опциональные проверки
        if cls.REQUIRE_DIGIT and not re.search(r'\d', plain_password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")

        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', plain_password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', plain_password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")

        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', plain_password):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ")

    @staticmethod
    def _hash_password(plain_password: str) -> str:
        """
        Хешировать пароль используя Django.
        """
        from django.contrib.auth.hashers import make_password
        return make_password(plain_password)

    def verify(self, plain_password: str) -> bool:
        """
        Проверить соответствует ли пароль хешу.
        """
        from django.contrib.auth.hashers import check_password
        return check_password(plain_password, self.hashed_value)

    def is_strong(self) -> bool:
        """
        Проверка силы пароля.
        """
        # Не можем проверить силу хеша
        return True

    def __str__(self) -> str:
        """Никогда не показываем хеш!"""
        return "Password(***)"

    def __repr__(self) -> str:
        return "Password(***)"

