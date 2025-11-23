import pytest
from apps.game.domain.value_objects.score import Score


class TestScore:

    def test_create_score_with_valid_value(self):
        """Создание Score с валидным значением"""
        score = Score(10)
        assert score.value == 10

    def test_create_zero_score(self):
        """Создание Score с нулевым значением"""
        score = Score(0)
        assert score.value == 0
        assert score.is_zero()

    def test_create_score_using_zero_factory(self):
        """Создание нулевого Score через фабричный метод"""
        score = Score.zero()
        assert score.value == 0
        assert score.is_zero()

    def test_cannot_create_score_with_negative_value(self):
        """Нельзя создать Score с отрицательным значением"""
        with pytest.raises(ValueError) as exc_info:
            Score(-10)

        assert "отрицательными" in str(exc_info.value).lower()

    def test_cannot_create_score_with_non_integer(self):
        """Нельзя создать Score с нецелым значением"""
        with pytest.raises(TypeError):
            Score(10.5)

    # ============ Тесты неизменяемости (immutability) ============

    def test_score_is_immutable(self):
        """Score должен быть неизменяемым"""
        score = Score(10)

        with pytest.raises(Exception):  # dataclass frozen=True вызывает FrozenInstanceError
            score.value = 20

    # ============ Тесты арифметических операций ============

    def test_add_two_scores(self):
        """Сложение двух Score объектов"""
        score1 = Score(10)
        score2 = Score(5)
        result = score1 + score2

        assert result.value == 15
        assert isinstance(result, Score)
        # Исходные объекты не изменились
        assert score1.value == 10
        assert score2.value == 5

    def test_add_score_and_int(self):
        """Сложение Score с int"""
        score = Score(10)
        result = score + 5

        assert result.value == 15
        assert isinstance(result, Score)

    def test_add_int_and_score(self):
        """Сложение int со Score (обратная операция)"""
        score = Score(10)
        result = 5 + score

        assert result.value == 15
        assert isinstance(result, Score)

    def test_sum_multiple_scores(self):
        """Суммирование нескольких Score через sum()"""
        scores = [Score(10), Score(20), Score(30)]
        total = sum(scores, Score.zero())

        assert total.value == 60

    def test_subtract_two_scores(self):
        """Вычитание двух Score объектов"""
        score1 = Score(10)
        score2 = Score(3)
        result = score1 - score2

        assert result.value == 7
        assert isinstance(result, Score)

    def test_subtract_score_and_int(self):
        """Вычитание int из Score"""
        score = Score(10)
        result = score - 3

        assert result.value == 7

    def test_subtract_with_negative_result_returns_zero(self):
        """Вычитание с отрицательным результатом возвращает 0"""
        score1 = Score(5)
        score2 = Score(10)
        result = score1 - score2

        assert result.value == 0  # Не -5, а 0

    def test_multiply_score_by_int(self):
        """Умножение Score на int"""
        score = Score(10)
        result = score * 2

        assert result.value == 20

    def test_multiply_score_by_float(self):
        """Умножение Score на float"""
        score = Score(10)
        result = score * 1.5

        assert result.value == 15

    def test_multiply_score_by_zero(self):
        """Умножение Score на 0"""
        score = Score(10)
        result = score * 0

        assert result.value == 0
        assert result.is_zero()

    def test_cannot_multiply_by_non_number(self):
        """Нельзя умножить Score на не-число"""
        score = Score(10)

        with pytest.raises(TypeError):
            score * "5"

    # ============ Тесты сравнения ============

    def test_equal_scores(self):
        """Равные Score объекты"""
        score1 = Score(10)
        score2 = Score(10)

        assert score1 == score2
        assert not (score1 != score2)

    def test_equal_score_and_int(self):
        """Сравнение Score с int"""
        score = Score(10)

        assert score == 10
        assert 10 == score.value

    def test_not_equal_scores(self):
        """Неравные Score объекты"""
        score1 = Score(10)
        score2 = Score(5)

        assert score1 != score2

    def test_less_than(self):
        """Меньше чем"""
        score1 = Score(5)
        score2 = Score(10)

        assert score1 < score2
        assert score1 < 10

    def test_less_than_or_equal(self):
        """Меньше или равно"""
        score1 = Score(10)
        score2 = Score(10)
        score3 = Score(5)

        assert score1 <= score2
        assert score3 <= score1

    def test_greater_than(self):
        """Больше чем"""
        score1 = Score(10)
        score2 = Score(5)

        assert score1 > score2
        assert score1 > 5

    def test_greater_than_or_equal(self):
        """Больше или равно"""
        score1 = Score(10)
        score2 = Score(10)
        score3 = Score(15)

        assert score1 >= score2
        assert score3 >= score1

    def test_cannot_compare_with_incompatible_type(self):
        """Нельзя сравнить Score с несовместимым типом"""
        score = Score(10)

        with pytest.raises(TypeError):
            score < "10"

    # ============ Тесты строковых представлений ============

    def test_str_representation(self):
        """Строковое представление Score"""
        score = Score(100)
        assert "100" in str(score)
        assert "очк" in str(score)

    def test_repr_representation(self):
        """Представление для отладки"""
        score = Score(100)
        assert "Score" in repr(score)
        assert "100" in repr(score)

    # ============ Тесты преобразований ============

    def test_convert_to_int(self):
        """Преобразование Score в int"""
        score = Score(42)
        assert int(score) == 42
        assert isinstance(int(score), int)

    # ============ Граничные случаи ============

    def test_very_large_score(self):
        """Очень большое значение Score"""
        score = Score(999999)
        assert score.value == 999999

    def test_score_operations_chain(self):
        """Цепочка операций со Score"""
        score = Score(10)
        result = ((score + 5) * 2) - 10

        # (10 + 5) * 2 - 10 = 15 * 2 - 10 = 30 - 10 = 20
        assert result.value == 20

    def test_score_in_collections(self):
        """Score в коллекциях"""
        scores = [Score(10), Score(20), Score(5)]
        sorted_scores = sorted(scores)

        assert sorted_scores[0].value == 5
        assert sorted_scores[1].value == 10
        assert sorted_scores[2].value == 20

    def test_score_as_dict_key(self):
        """Score как ключ словаря (должен быть hashable)"""
        score_map = {
            Score(10): "bronze",
            Score(20): "silver",
            Score(30): "gold"
        }

        assert score_map[Score(10)] == "bronze"
        assert score_map[Score(20)] == "silver"

