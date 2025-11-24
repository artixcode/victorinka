from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionText:
    """
    Value Object для текста вопроса.
    """
    value: str

    MIN_LENGTH = 10
    MAX_LENGTH = 1000
    REQUIRE_QUESTION_MARK = False  # Можно включить для строгости

    def __post_init__(self):
        """Валидация при создании"""
        # Очистка от лишних пробелов
        cleaned = self.value.strip()
        object.__setattr__(self, 'value', cleaned)

        # Проверки
        if not self.value:
            raise ValueError("Текст вопроса не может быть пустым")

        if len(self.value) < self.MIN_LENGTH:
            raise ValueError(
                f"Текст вопроса слишком короткий "
                f"(минимум {self.MIN_LENGTH} символов, сейчас {len(self.value)})"
            )

        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(
                f"Текст вопроса слишком длинный "
                f"(максимум {self.MAX_LENGTH} символов, сейчас {len(self.value)})"
            )

        if self.REQUIRE_QUESTION_MARK and not self.value.endswith('?'):
            raise ValueError("Вопрос должен заканчиваться вопросительным знаком")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        preview = self.value[:50] + "..." if len(self.value) > 50 else self.value
        return f"QuestionText('{preview}')"

    @property
    def word_count(self) -> int:
        """Количество слов в вопросе"""
        return len(self.value.split())

    @property
    def is_short(self) -> bool:
        """Короткий вопрос (меньше 50 символов)"""
        return len(self.value) < 50

