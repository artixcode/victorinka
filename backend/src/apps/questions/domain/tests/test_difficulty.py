import pytest
from apps.questions.domain.value_objects.difficulty import Difficulty, DifficultyLevel


class TestDifficulty:
    """Тесты для Difficulty Value Object"""

    def test_create_easy(self):
        """Тест создания лёгкой сложности"""
        diff = Difficulty.easy()
        assert diff.level == DifficultyLevel.EASY

    def test_create_medium(self):
        """Тест создания средней сложности"""
        diff = Difficulty.medium()
        assert diff.level == DifficultyLevel.MEDIUM

    def test_create_hard(self):
        """Тест создания сложной сложности"""
        diff = Difficulty.hard()
        assert diff.level == DifficultyLevel.HARD

    def test_from_string_easy(self):
        """Тест создания из строки (easy)"""
        diff = Difficulty.from_string("easy")
        assert diff.level == DifficultyLevel.EASY

    def test_from_string_case_insensitive(self):
        """Тест регистронезависимости"""
        diff = Difficulty.from_string("MEDIUM")
        assert diff.level == DifficultyLevel.MEDIUM

    def test_from_string_invalid(self):
        """Тест: неверная строка"""
        with pytest.raises(ValueError, match="Неизвестный уровень"):
            Difficulty.from_string("invalid")

    def test_recommended_points_easy(self):
        """Тест автоматических очков для easy"""
        diff = Difficulty.easy()
        assert diff.recommended_points() == 5

    def test_recommended_points_medium(self):
        """Тест автоматических очков для medium"""
        diff = Difficulty.medium()
        assert diff.recommended_points() == 10

    def test_recommended_points_hard(self):
        """Тест автоматических очков для hard"""
        diff = Difficulty.hard()
        assert diff.recommended_points() == 15

    def test_is_easy(self):
        """Тест проверки is_easy"""
        diff = Difficulty.easy()
        assert diff.is_easy() is True
        assert diff.is_medium() is False

    def test_is_medium(self):
        """Тест проверки is_medium"""
        diff = Difficulty.medium()
        assert diff.is_medium() is True
        assert diff.is_hard() is False

    def test_is_hard(self):
        """Тест проверки is_hard"""
        diff = Difficulty.hard()
        assert diff.is_hard() is True
        assert diff.is_easy() is False

    def test_equality(self):
        """Тест сравнения"""
        diff1 = Difficulty.medium()
        diff2 = Difficulty.medium()
        assert diff1 == diff2

    def test_comparison_less_than(self):
        """Тест сравнения (easy < medium < hard)"""
        easy = Difficulty.easy()
        medium = Difficulty.medium()
        hard = Difficulty.hard()

        assert easy < medium
        assert medium < hard
        assert easy < hard

    def test_str_representation(self):
        """Тест строкового представления"""
        diff = Difficulty.medium()
        assert str(diff) == "Средний"

