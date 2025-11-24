from dataclasses import dataclass
import secrets
import string
import re


@dataclass(frozen=True)
class InviteCode:
    """
    Value Object для кода приглашения.
    """
    value: str

    DEFAULT_LENGTH = 6
    ALLOWED_CHARS = string.ascii_uppercase + string.digits
    # Убираем похожие символы для лучшей читаемости
    SAFE_CHARS = ''.join(c for c in ALLOWED_CHARS if c not in '01OILZ')

    def __post_init__(self):
        # Нормализация к uppercase
        normalized = self.value.upper().strip()
        object.__setattr__(self, 'value', normalized)

        # Валидация
        if not self.value:
            raise ValueError("Код приглашения не может быть пустым")

        if len(self.value) != self.DEFAULT_LENGTH:
            raise ValueError(
                f"Код приглашения должен быть {self.DEFAULT_LENGTH} символов, "
                f"получено {len(self.value)}"
            )

        if not re.match(r'^[A-Z0-9]+$', self.value):
            raise ValueError(
                "Код приглашения может содержать только заглавные буквы и цифры"
            )

    @classmethod
    def generate(cls, use_safe_chars: bool = True) -> 'InviteCode':
        """
        Сгенерировать новый уникальный код.
        """
        alphabet = cls.SAFE_CHARS if use_safe_chars else cls.ALLOWED_CHARS
        code_value = ''.join(
            secrets.choice(alphabet) for _ in range(cls.DEFAULT_LENGTH)
        )
        return cls(code_value)

    @classmethod
    def from_string(cls, value: str) -> 'InviteCode':
        """
        Создать из строки с валидацией.
        """
        return cls(value)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"InviteCode('{self.value}')"

    def __eq__(self, other) -> bool:
        """Сравнение кодов"""
        if isinstance(other, InviteCode):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.upper()
        return False

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def is_valid(self) -> bool:
        return True

    def formatted(self, separator: str = '-') -> str:
        """
        Форматированный вид кода (для удобства чтения).
        """
        mid = len(self.value) // 2
        return f"{self.value[:mid]}{separator}{self.value[mid:]}"

