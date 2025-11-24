from dataclasses import dataclass
from enum import Enum


class DifficultyLevel(str, Enum):
    """Перечисление уровней сложности"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def from_string(cls, value: str) -> 'DifficultyLevel':
        """Создать из строки"""
        value_lower = value.lower()
        for level in cls:
            if level.value == value_lower:
                return level
        raise ValueError(f"Неизвестный уровень сложности: {value}")

    def to_display(self) -> str:
        """Человекочитаемое название"""
        display_map = {
            self.EASY: "Лёгкий",
            self.MEDIUM: "Средний",
            self.HARD: "Сложный"
        }
        return display_map[self]


@dataclass(frozen=True)
class Difficulty:
    """
    Value Object для сложности вопроса.
    """
    level: DifficultyLevel

    # Рекомендуемые очки за правильный ответ
    POINTS_MAP = {
        DifficultyLevel.EASY: 5,
        DifficultyLevel.MEDIUM: 10,
        DifficultyLevel.HARD: 15,
    }

    def __post_init__(self):
        """Валидация"""
        if not isinstance(self.level, DifficultyLevel):
            raise ValueError(
                f"level должен быть экземпляром DifficultyLevel, "
                f"получен {type(self.level)}"
            )

    @classmethod
    def easy(cls) -> 'Difficulty':
        """Создать лёгкую сложность"""
        return cls(DifficultyLevel.EASY)

    @classmethod
    def medium(cls) -> 'Difficulty':
        """Создать среднюю сложность"""
        return cls(DifficultyLevel.MEDIUM)

    @classmethod
    def hard(cls) -> 'Difficulty':
        """Создать сложную сложность"""
        return cls(DifficultyLevel.HARD)

    @classmethod
    def from_string(cls, value: str) -> 'Difficulty':
        """
        Создать из строки.
        """
        level = DifficultyLevel.from_string(value)
        return cls(level)

    def recommended_points(self) -> int:
        """
        Рекомендуемое количество очков для этой сложности.
        """
        return self.POINTS_MAP[self.level]

    def is_easy(self) -> bool:
        """Проверка на лёгкий уровень"""
        return self.level == DifficultyLevel.EASY

    def is_medium(self) -> bool:
        """Проверка на средний уровень"""
        return self.level == DifficultyLevel.MEDIUM

    def is_hard(self) -> bool:
        """Проверка на сложный уровень"""
        return self.level == DifficultyLevel.HARD

    def __str__(self) -> str:
        return self.level.to_display()

    def __repr__(self) -> str:
        return f"Difficulty({self.level.value})"

    def __eq__(self, other) -> bool:
        """Сравнение"""
        if isinstance(other, Difficulty):
            return self.level == other.level
        return False

    def __lt__(self, other: 'Difficulty') -> bool:
        """Сравнение для сортировки (easy < medium < hard)"""
        order = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
        return order.index(self.level) < order.index(other.level)

