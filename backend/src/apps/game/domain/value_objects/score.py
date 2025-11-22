from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Score:
    """
    Объект-значение для очков игрока.

    Особенности:
    - Неизменяемый (frozen=True)
    - Не имеет идентичности (два Score с одинаковым value - это один и тот же объект)
    - Инкапсулирует валидацию
    - Поддерживает арифметические операции
    """
    value: int

    def __post_init__(self):
        """Валидация при создании объекта"""
        if self.value < 0:
            raise ValueError("Очки не могут быть отрицательными")
        if not isinstance(self.value, int):
            raise TypeError("Очки должны быть целым числом")

    def __add__(self, other: Union['Score', int]) -> 'Score':
        if isinstance(other, Score):
            return Score(self.value + other.value)
        elif isinstance(other, int):
            return Score(self.value + other)
        else:
            raise TypeError(f"Невозможно сложить Score с {type(other)}")

    def __radd__(self, other: Union['Score', int]) -> 'Score':
        return self.__add__(other)

    def __sub__(self, other: Union['Score', int]) -> 'Score':
        if isinstance(other, Score):
            result = self.value - other.value
        elif isinstance(other, int):
            result = self.value - other
        else:
            raise TypeError(f"Невозможно вычесть {type(other)} из Score")

        # Очки не могут быть отрицательными
        return Score(max(0, result))

    def __mul__(self, multiplier: Union[int, float]) -> 'Score':

        if not isinstance(multiplier, (int, float)):
            raise TypeError(f"Множитель должен быть числом, получен {type(multiplier)}")

        return Score(int(self.value * multiplier))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Score):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False

    def __lt__(self, other: Union['Score', int]) -> bool:
        if isinstance(other, Score):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value < other
        raise TypeError(f"Невозможно сравнить Score с {type(other)}")

    def __le__(self, other: Union['Score', int]) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other: Union['Score', int]) -> bool:
        if isinstance(other, Score):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        raise TypeError(f"Невозможно сравнить Score с {type(other)}")

    def __ge__(self, other: Union['Score', int]) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __str__(self) -> str:
        return f"{self.value} очк."

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Score(value={self.value})"

    def __int__(self) -> int:
        return self.value

    @classmethod
    def zero(cls) -> 'Score':
        return cls(0)

    def is_zero(self) -> bool:
        return self.value == 0

