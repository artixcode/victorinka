import pytest
from apps.users.domain.value_objects.password import Password


class TestPassword:
    """Тесты для Password Value Object"""

    def test_create_valid_password(self):
        """Тест создания валидного пароля"""
        pwd = Password.create("password123")
        assert pwd.hashed_value is not None
        assert pwd.hashed_value != "password123"  # Должен быть хеш

    def test_password_too_short(self):
        """Тест: слишком короткий пароль"""
        with pytest.raises(ValueError, match="слишком короткий"):
            Password.create("123")

    def test_password_minimum_length(self):
        """Тест минимальной длины"""
        pwd = Password.create("12345678")  # Ровно 8 символов
        assert pwd.hashed_value is not None

    def test_password_empty(self):
        """Тест: пустой пароль"""
        with pytest.raises(ValueError, match="не может быть пустым"):
            Password.create("")

    def test_password_too_long(self):
        """Тест: слишком длинный пароль"""
        long_pwd = "a" * 130
        with pytest.raises(ValueError, match="слишком длинный"):
            Password.create(long_pwd)

    def test_password_verify_correct(self):
        """Тест проверки правильного пароля"""
        pwd = Password.create("password123")
        assert pwd.verify("password123") is True

    def test_password_verify_incorrect(self):
        """Тест проверки неправильного пароля"""
        pwd = Password.create("password123")
        assert pwd.verify("wrong_password") is False

    def test_password_from_hash(self):
        """Тест создания из хеша"""
        pwd1 = Password.create("password123")
        pwd2 = Password.from_hash(pwd1.hashed_value)
        assert pwd2.hashed_value == pwd1.hashed_value

    def test_password_str_hides_hash(self):
        """Тест что str не показывает хеш"""
        pwd = Password.create("password123")
        assert str(pwd) == "Password(***)"

    def test_password_repr_hides_hash(self):
        """Тест что repr не показывает хеш"""
        pwd = Password.create("password123")
        assert repr(pwd) == "Password(***)"

