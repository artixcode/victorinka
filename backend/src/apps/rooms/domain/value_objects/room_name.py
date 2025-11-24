from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RoomName:
    """
    Value Object для названия комнаты.
    """
    value: str

    MIN_LENGTH = 3
    MAX_LENGTH = 120

    # Разрешённые символы: буквы, цифры, пробелы, дефисы, подчёркивания
    ALLOWED_PATTERN = re.compile(r'^[\w\s\-]+$', re.UNICODE)

    def __post_init__(self):
        """Валидация и нормализация"""
        # Очистка от лишних пробелов
        cleaned = ' '.join(self.value.split())
        object.__setattr__(self, 'value', cleaned)

        # Валидация
        if not self.value:
            raise ValueError("Название комнаты не может быть пустым")

        if len(self.value) < self.MIN_LENGTH:
            raise ValueError(
                f"Название комнаты слишком короткое "
                f"(минимум {self.MIN_LENGTH} символа, сейчас {len(self.value)})"
            )

        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(
                f"Название комнаты слишком длинное "
                f"(максимум {self.MAX_LENGTH} символов, сейчас {len(self.value)})"
            )

        if not self.ALLOWED_PATTERN.match(self.value):
            raise ValueError(
                "Название комнаты может содержать только буквы, цифры, "
                "пробелы, дефисы и подчёркивания"
            )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"RoomName('{self.value}')"

    @property
    def word_count(self) -> int:
        """Количество слов в названии"""
        return len(self.value.split())

    @property
    def is_short(self) -> bool:
        """Короткое название (меньше 20 символов)"""
        return len(self.value) < 20

    def truncate(self, max_length: int = 50) -> str:
        """
        Обрезать название до указанной длины.
        """
        if len(self.value) <= max_length:
            return self.value
        return self.value[:max_length - 3] + "..."

