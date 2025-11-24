import pytest
from apps.game.domain.services.score_calculator import ScoreCalculator
from apps.game.domain.value_objects.score import Score
from apps.game.domain.exceptions import GameRuleViolationException


class TestScoreCalculator:
    """Тесты для ScoreCalculator"""

    def setup_method(self):
        """Инициализация перед каждым тестом"""
        self.calculator = ScoreCalculator()

    # ============ Тесты базовых сценариев ============

    def test_incorrect_answer_returns_zero_points(self):
        """Неправильный ответ должен давать 0 очков"""
        score = self.calculator.calculate(
            is_correct=False,
            base_points=10,
            time_taken=5.0,
            time_limit=30,
            is_first_answer=False
        )

        assert score.value == 0
        assert score == Score.zero()

    def test_correct_answer_with_no_bonuses(self):
        """Правильный ответ без бонусов (ответили на последней секунде)"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=30.0,  # Всё время использовано
            time_limit=30,
            is_first_answer=False
        )

        assert score.value == 10  # Только базовые очки

    def test_correct_answer_with_speed_bonus(self):
        """Правильный ответ с бонусом за скорость"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=0.0,  # Мгновенный ответ
            time_limit=30,
            is_first_answer=False
        )

        # base=10 + speed_bonus=5 (50% от 10) = 15
        assert score.value == 15

    def test_correct_answer_with_first_answer_bonus(self):
        """Правильный ответ с бонусом за первый ответ"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=30.0,
            time_limit=30,
            is_first_answer=True
        )

        # base=10 + first_bonus=5 (50% от 10) = 15
        assert score.value == 15

    def test_correct_answer_with_all_bonuses(self):
        """Правильный ответ со всеми бонусами"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=0.0,  # Мгновенный ответ
            time_limit=30,
            is_first_answer=True
        )

        # base=10 + speed=5 + first=5 = 20
        assert score.value == 20

    # ============ Тесты расчёта бонуса за скорость ============

    def test_speed_bonus_calculation_half_time(self):
        """Бонус за скорость при ответе за половину времени"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=15.0,  # Половина времени
            time_limit=30,
            is_first_answer=False
        )

        # speed_bonus = 10 * ((30-15)/30) * 0.5 = 10 * 0.5 * 0.5 = 2.5 -> 2
        assert score.value == 12  # 10 + 2

    def test_speed_bonus_calculation_quarter_time(self):
        """Бонус за скорость при ответе за четверть времени"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=20,
            time_taken=7.5,  # 1/4 времени
            time_limit=30,
            is_first_answer=False
        )

        # speed_bonus = 20 * ((30-7.5)/30) * 0.5 = 20 * 0.75 * 0.5 = 7.5 -> 7
        assert score.value == 27  # 20 + 7

    def test_no_speed_bonus_when_time_exceeded(self):
        """Нет бонуса за скорость при превышении времени"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=35.0,  # Превысили лимит
            time_limit=30,
            is_first_answer=False
        )

        assert score.value == 10  # Только базовые очки

    # ============ Тесты валидации ============

    def test_negative_base_points_raises_exception(self):
        """Отрицательные базовые очки должны вызывать исключение"""
        with pytest.raises(GameRuleViolationException) as exc_info:
            self.calculator.calculate(
                is_correct=True,
                base_points=-10,
                time_taken=5.0,
                time_limit=30,
                is_first_answer=False
            )

        assert "отрицательными" in str(exc_info.value).lower()

    def test_negative_time_taken_raises_exception(self):
        """Отрицательное время ответа должно вызывать исключение"""
        with pytest.raises(GameRuleViolationException) as exc_info:
            self.calculator.calculate(
                is_correct=True,
                base_points=10,
                time_taken=-5.0,
                time_limit=30,
                is_first_answer=False
            )

        assert "отрицательным" in str(exc_info.value).lower()

    def test_zero_time_limit_raises_exception(self):
        """Нулевой лимит времени должен вызывать исключение"""
        with pytest.raises(GameRuleViolationException) as exc_info:
            self.calculator.calculate(
                is_correct=True,
                base_points=10,
                time_taken=5.0,
                time_limit=0,
                is_first_answer=False
            )

        assert "положительным" in str(exc_info.value).lower()

    # ============ Тесты метода get_bonus_details ============

    def test_get_bonus_details_for_correct_answer(self):
        """Детали расчёта для правильного ответа"""
        details = self.calculator.get_bonus_details(
            is_correct=True,
            base_points=10,
            time_taken=10.0,
            time_limit=30,
            is_first_answer=True
        )

        assert details["base"] == 10
        assert details["speed_bonus"] > 0
        assert details["first_answer_bonus"] == 5
        assert details["total"] == details["base"] + details["speed_bonus"] + details["first_answer_bonus"]
        assert details["is_first_answer"] is True

    def test_get_bonus_details_for_incorrect_answer(self):
        """Детали расчёта для неправильного ответа"""
        details = self.calculator.get_bonus_details(
            is_correct=False,
            base_points=10,
            time_taken=5.0,
            time_limit=30,
            is_first_answer=False
        )

        assert details["total"] == 0
        assert details["base"] == 0
        assert details["speed_bonus"] == 0
        assert details["first_answer_bonus"] == 0
        assert "reason" in details

    # ============ Тесты кастомных множителей ============

    def test_custom_speed_bonus_multiplier(self):
        """Тест с кастомным множителем бонуса за скорость"""
        calculator = ScoreCalculator(speed_bonus_multiplier=1.0)  # 100% вместо 50%

        score = calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=0.0,
            time_limit=30,
            is_first_answer=False
        )

        # base=10 + speed=10 (100% от 10) = 20
        assert score.value == 20

    def test_custom_first_answer_bonus_multiplier(self):
        """Тест с кастомным множителем бонуса за первый ответ"""
        calculator = ScoreCalculator(first_answer_bonus_multiplier=1.0)  # 100% вместо 50%

        score = calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=30.0,
            time_limit=30,
            is_first_answer=True
        )

        # base=10 + first=10 (100% от 10) = 20
        assert score.value == 20

    # ============ Граничные случаи ============

    def test_zero_base_points(self):
        """Вопрос с нулевыми базовыми очками"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=0,
            time_taken=5.0,
            time_limit=30,
            is_first_answer=True
        )

        assert score.value == 0

    def test_very_high_base_points(self):
        """Вопрос с очень высокими базовыми очками"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=1000,
            time_taken=0.0,
            time_limit=30,
            is_first_answer=True
        )

        # base=1000 + speed=500 + first=500 = 2000
        assert score.value == 2000

    def test_fractional_seconds(self):
        """Время в долях секунды"""
        score = self.calculator.calculate(
            is_correct=True,
            base_points=10,
            time_taken=0.5,  # Полсекунды
            time_limit=30,
            is_first_answer=False
        )

        assert score.value > 10  # Должен быть бонус за скорость

