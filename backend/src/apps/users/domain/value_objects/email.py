import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Value Object для email адреса.
    """
    value: str

    # Простой regex для базовой валидации email
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __post_init__(self):
        """Валидация и нормализация при создании"""
        # Нормализуем к lowercase
        normalized = self.value.lower().strip()

        # Заменяем значение через object.__setattr__ (т.к. frozen=True)
        object.__setattr__(self, 'value', normalized)

        # Валидация
        if not self.value:
            raise ValueError("Email не может быть пустым")

        if len(self.value) > 254:
            raise ValueError("Email слишком длинный (максимум 254 символа)")

        if not self.EMAIL_REGEX.match(self.value):
            raise ValueError(f"Некорректный формат email: {self.value}")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Email('{self.value}')"

    @property
    def domain(self) -> str:
        """Получить доменную часть email"""
        return self.value.split('@')[1]

    @property
    def local_part(self) -> str:
        """Получить локальную часть email (до @)"""
        return self.value.split('@')[0]

