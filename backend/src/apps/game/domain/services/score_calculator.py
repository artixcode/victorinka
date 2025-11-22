from typing import Optional
from ..value_objects.score import Score
from ..exceptions import GameRuleViolationException


class ScoreCalculator:
    """
    1. За неправильный ответ - 0 очков
    2. За правильный ответ - базовые очки вопроса
    3. Бонус за скорость ответа - до +50% к базовым очкам
    4. Бонус за первый правильный ответ - +50% к базовым очкам
    """

    SPEED_BONUS_MULTIPLIER: float = 0.5  # Максимум +50% за скорость
    FIRST_ANSWER_BONUS_MULTIPLIER: float = 0.5  # +50% за первый ответ

    def __init__(
        self,
        speed_bonus_multiplier: Optional[float] = None,
        first_answer_bonus_multiplier: Optional[float] = None
    ):
        self.speed_bonus_multiplier = speed_bonus_multiplier or self.SPEED_BONUS_MULTIPLIER
        self.first_answer_bonus_multiplier = first_answer_bonus_multiplier or self.FIRST_ANSWER_BONUS_MULTIPLIER

    def calculate(
        self,
        is_correct: bool,
        base_points: int,
        time_taken: float,
        time_limit: int,
        is_first_answer: bool = False
    ) -> Score:
        # Валидация входных параметров
        self._validate_parameters(base_points, time_taken, time_limit)

        # Неправильный ответ = 0 очков
        if not is_correct:
            return Score.zero()

        # Начинаем с базовых очков
        total_points = base_points

        # Бонус за скорость ответа
        speed_bonus = self._calculate_speed_bonus(
            base_points=base_points,
            time_taken=time_taken,
            time_limit=time_limit
        )
        total_points += speed_bonus

        # Бонус за первый правильный ответ
        if is_first_answer:
            first_answer_bonus = self._calculate_first_answer_bonus(base_points)
            total_points += first_answer_bonus

        return Score(total_points)

    def _validate_parameters(
        self,
        base_points: int,
        time_taken: float,
        time_limit: int
    ) -> None:
        if base_points < 0:
            raise GameRuleViolationException(
                f"Базовые очки не могут быть отрицательными: {base_points}"
            )

        if time_taken < 0:
            raise GameRuleViolationException(
                f"Время ответа не может быть отрицательным: {time_taken}"
            )

        if time_limit <= 0:
            raise GameRuleViolationException(
                f"Лимит времени должен быть положительным: {time_limit}"
            )

    def _calculate_speed_bonus(
        self,
        base_points: int,
        time_taken: float,
        time_limit: int
    ) -> int:
        """
        Рассчитать бонус за скорость ответа.

        Формула: bonus = base_points * ((time_limit - time_taken) / time_limit) * multiplier

        Чем быстрее ответ, тем выше бонус.
        Если ответили за всё время или позже - бонус = 0.
        """
        if time_taken >= time_limit:
            return 0

        # Процент оставшегося времени
        time_ratio = (time_limit - time_taken) / time_limit

        # Бонус пропорционален оставшемуся времени
        bonus = int(base_points * time_ratio * self.speed_bonus_multiplier)

        return bonus

    def _calculate_first_answer_bonus(self, base_points: int) -> int:
        return int(base_points * self.first_answer_bonus_multiplier)

    def get_bonus_details(
        self,
        is_correct: bool,
        base_points: int,
        time_taken: float,
        time_limit: int,
        is_first_answer: bool = False
    ) -> dict:
        if not is_correct:
            return {
                "total": 0,
                "base": 0,
                "speed_bonus": 0,
                "first_answer_bonus": 0,
                "reason": "Неправильный ответ"
            }

        speed_bonus = self._calculate_speed_bonus(base_points, time_taken, time_limit)
        first_answer_bonus = self._calculate_first_answer_bonus(base_points) if is_first_answer else 0

        return {
            "total": base_points + speed_bonus + first_answer_bonus,
            "base": base_points,
            "speed_bonus": speed_bonus,
            "first_answer_bonus": first_answer_bonus,
            "time_taken": time_taken,
            "time_limit": time_limit,
            "is_first_answer": is_first_answer
        }

