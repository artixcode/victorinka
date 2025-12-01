import pytest

from apps.rooms.domain.value_objects.room_name import RoomName


class TestRoomName:
    """Тесты для RoomName Value Object"""

    def test_valid_name_min_length(self):
        """Корректное имя с минимальной длиной"""
        name = "ABC"  # MIN_LENGTH = 3
        obj = RoomName(name)
        assert obj.value == name

    def test_whitespace_normalization(self):
        """Множественные пробелы схлопываются в один"""
        obj = RoomName("  Моя    комната   тест  ")
        assert obj.value == "Моя комната тест"

    def test_empty_name_raises(self):
        """Пустое имя (после нормализации) запрещено"""
        with pytest.raises(ValueError, match="не может быть пустым"):
            RoomName("   ")

    def test_too_short_name_raises(self):
        """Имя короче MIN_LENGTH → ошибка"""
        too_short = "AB"  # длина = 2
        with pytest.raises(ValueError, match="слишком короткое"):
            RoomName(too_short)

    def test_too_long_name_raises(self):
        """Имя длиннее MAX_LENGTH → ошибка"""
        too_long = "X" * (RoomName.MAX_LENGTH + 1)
        with pytest.raises(ValueError, match="слишком длинное"):
            RoomName(too_long)

    def test_invalid_characters_raise(self):
        """Недопустимые символы (например, '!') → ошибка"""
        with pytest.raises(ValueError, match="буквы, цифры"):
            RoomName("Комната!!!")

    def test_word_count_and_is_short(self):
        """Проверяем word_count и is_short"""
        obj = RoomName("Очень короткое имя")
        assert obj.word_count == 3
        assert obj.is_short is True  # < 20 символов

    def test_truncate_returns_full_when_short(self):
        """truncate ничего не режет, если длина меньше лимита"""
        name = "Нормальное имя комнаты"
        obj = RoomName(name)
        assert obj.truncate(50) == name

    def test_truncate_cuts_and_adds_ellipsis(self):
        """truncate режет строку и добавляет '...'"""
        name = "Очень длинное название комнаты для проверки truncate"
        obj = RoomName(name)
        truncated = obj.truncate(20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
