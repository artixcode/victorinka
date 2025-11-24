import pytest
from apps.users.domain.value_objects.email import Email


class TestEmail:
    """Тесты для Email Value Object"""

    def test_valid_email(self):
        """Тест валидного email"""
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_email_normalization_lowercase(self):
        """Тест нормализации к lowercase"""
        email = Email("USER@EXAMPLE.COM")
        assert email.value == "user@example.com"

    def test_email_strip_whitespace(self):
        """Тест удаления пробелов"""
        email = Email("  user@example.com  ")
        assert email.value == "user@example.com"

    def test_empty_email_raises_error(self):
        """Тест: пустой email вызывает ошибку"""
        with pytest.raises(ValueError, match="не может быть пустым"):
            Email("")

    def test_invalid_format_raises_error(self):
        """Тест: неверный формат вызывает ошибку"""
        with pytest.raises(ValueError, match="Некорректный формат"):
            Email("invalid-email")

    def test_missing_at_symbol(self):
        """Тест: отсутствие @ вызывает ошибку"""
        with pytest.raises(ValueError):
            Email("userexample.com")

    def test_missing_domain(self):
        """Тест: отсутствие домена вызывает ошибку"""
        with pytest.raises(ValueError):
            Email("user@")

    def test_too_long_email(self):
        """Тест: слишком длинный email"""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValueError, match="слишком длинный"):
            Email(long_email)

    def test_email_domain_property(self):
        """Тест свойства domain"""
        email = Email("user@example.com")
        assert email.domain == "example.com"

    def test_email_local_part_property(self):
        """Тест свойства local_part"""
        email = Email("user@example.com")
        assert email.local_part == "user"

    def test_email_str_representation(self):
        """Тест строкового представления"""
        email = Email("user@example.com")
        assert str(email) == "user@example.com"

    def test_email_repr_representation(self):
        """Тест repr представления"""
        email = Email("user@example.com")
        assert repr(email) == "Email('user@example.com')"

    def test_email_equality(self):
        """Тест сравнения email"""
        email1 = Email("user@example.com")
        email2 = Email("USER@EXAMPLE.COM")
        assert email1.value == email2.value  # Оба нормализованы

    def test_email_immutability(self):
        """Тест неизменяемости"""
        email = Email("user@example.com")
        # dataclass с frozen=True не позволяет изменять
        with pytest.raises(AttributeError):
            email.value = "new@example.com"

