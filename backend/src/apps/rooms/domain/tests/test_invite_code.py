import pytest
from apps.rooms.domain.value_objects.invite_code import InviteCode


class TestInviteCode:
    """Тесты для InviteCode Value Object"""

    def test_valid_code(self):
        """Тест валидного кода"""
        code = InviteCode("ABC123")
        assert code.value == "ABC123"

    def test_code_normalization_uppercase(self):
        """Тест нормализации к uppercase"""
        code = InviteCode("abc123")
        assert code.value == "ABC123"

    def test_code_strip_whitespace(self):
        """Тест удаления пробелов"""
        code = InviteCode("  ABC123  ")
        assert code.value == "ABC123"

    def test_code_length_validation(self):
        """Тест валидации длины (должно быть 6)"""
        with pytest.raises(ValueError, match="6 символов"):
            InviteCode("ABC")

    def test_empty_code(self):
        """Тест: пустой код"""
        with pytest.raises(ValueError, match="не может быть пустым"):
            InviteCode("")

    def test_invalid_characters(self):
        """Тест: недопустимые символы"""
        with pytest.raises(ValueError, match="только заглавные буквы"):
            InviteCode("ABC@12")

    def test_generate_code(self):
        """Тест генерации кода"""
        code = InviteCode.generate()
        assert len(code.value) == 6
        assert code.value.isupper()
        assert code.value.isalnum()

    def test_generate_safe_chars(self):
        """Тест что генерация не использует похожие символы"""
        # Генерируем много кодов
        for _ in range(100):
            code = InviteCode.generate(use_safe_chars=True)
            # Проверяем что нет похожих символов
            for char in ['0', 'O', 'I', 'L', 'Z', '1']:
                assert char not in code.value

    def test_from_string(self):
        """Тест создания из строки"""
        code = InviteCode.from_string("ABC123")
        assert code.value == "ABC123"

    def test_equality_with_code(self):
        """Тест сравнения с другим кодом"""
        code1 = InviteCode("ABC123")
        code2 = InviteCode("ABC123")
        assert code1 == code2

    def test_equality_with_string(self):
        """Тест сравнения со строкой"""
        code = InviteCode("ABC123")
        assert code == "ABC123"
        assert code == "abc123"  # Case insensitive

    def test_formatted_output(self):
        """Тест форматированного вывода"""
        code = InviteCode("ABC123")
        assert code.formatted() == "ABC-123"

    def test_formatted_custom_separator(self):
        """Тест форматирования с кастомным разделителем"""
        code = InviteCode("ABC123")
        assert code.formatted(separator="_") == "ABC_123"

    def test_str_representation(self):
        """Тест строкового представления"""
        code = InviteCode("ABC123")
        assert str(code) == "ABC123"

    def test_hash_for_dict(self):
        """Тест что код можно использовать в словаре"""
        code = InviteCode("ABC123")
        d = {code: "room"}
        assert d[code] == "room"

