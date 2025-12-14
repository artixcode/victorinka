import pytest

from apps.questions.domain.value_objects.question_text import QuestionText


class TestQuestionText:
    """Тесты для QuestionText Value Object"""

    def test_valid_min_length_text(self):
        """Создание с минимальной допустимой длиной"""
        text = "a" * QuestionText.MIN_LENGTH
        obj = QuestionText(text)
        assert obj.value == text

    def test_strips_whitespace(self):
        """Лишние пробелы по краям обрезаются"""
        obj = QuestionText("   Какой-то вопрос?   ")
        assert obj.value == "Какой-то вопрос?"

    def test_empty_text_raises_error(self):
        """Пустой текст (после strip) запрещён"""
        with pytest.raises(ValueError, match="не может быть пустым"):
            QuestionText("   ")

    def test_too_short_text_raises_error(self):
        """Текст короче MIN_LENGTH → ошибка"""
        too_short = "a" * (QuestionText.MIN_LENGTH - 1)
        with pytest.raises(ValueError, match="слишком короткий"):
            QuestionText(too_short)

    def test_too_long_text_raises_error(self):
        """Текст длиннее MAX_LENGTH → ошибка"""
        too_long = "a" * (QuestionText.MAX_LENGTH + 1)
        with pytest.raises(ValueError, match="слишком длинный"):
            QuestionText(too_long)

    def test_word_count_and_is_short(self):
        """Проверка word_count и is_short"""
        obj = QuestionText("Сколько будет два плюс два?")
        # "Сколько", "будет", "два", "плюс", "два?" → 5 слов
        assert obj.word_count == 5
        assert obj.is_short is True

    def test_repr_contains_preview(self):
        """repr содержит укороченный текст без падения"""
        text = "a" * 80
        obj = QuestionText(text)
        r = repr(obj)
        assert "QuestionText(" in r
        assert "..." in r or len(text) <= 50
