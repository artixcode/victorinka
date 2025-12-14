import pytest

from apps.questions.application.services.create_question_service import (
    CreateQuestionService,
)
from apps.questions.domain.value_objects.difficulty import Difficulty
from apps.questions.models import Question


@pytest.mark.django_db
def test_create_question_with_defaults_success(user):
    """
    Успешное создание вопроса:
    - очки берутся из Difficulty (easy -> 5)
    - создаются варианты ответа
    """
    service = CreateQuestionService()

    options = [
        {"text": "3", "is_correct": False},
        {"text": "4", "is_correct": True},
    ]

    question = service.execute(
        author_id=user.id,
        text="   Сколько будет 2 + 2?   ",
        difficulty="easy",
        options=options,
    )

    assert Question.objects.count() == 1
    assert question.author_id == user.id
    # QuestionText обрезает пробелы
    assert question.text == "Сколько будет 2 + 2?"
    # очки по умолчанию из Difficulty
    assert question.points == Difficulty.from_string("easy").recommended_points()
    assert question.options.count() == 2
    assert question.options.filter(is_correct=True).count() == 1


@pytest.mark.django_db
def test_create_question_with_custom_points_success(user):
    """Если points передан явно — используется он, а не recommended_points"""
    service = CreateQuestionService()

    options = [
        {"text": "Ответ 1", "is_correct": True},
        {"text": "Ответ 2", "is_correct": False},
    ]

    question = service.execute(
        author_id=user.id,
        text="Какой-то вопрос?",
        difficulty="medium",
        options=options,
        points=42,
    )

    assert question.points == 42


@pytest.mark.django_db
def test_create_question_with_non_positive_points_raises(user):
    """Очки <= 0 → ValueError"""
    service = CreateQuestionService()

    options = [
        {"text": "Ответ 1", "is_correct": True},
        {"text": "Ответ 2", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
            points=0,
        )


@pytest.mark.django_db
def test_create_question_not_enough_options_raises(user):
    """Меньше 2-х вариантов → ошибка"""
    service = CreateQuestionService()

    options = [
        {"text": "Один ответ", "is_correct": True},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )


@pytest.mark.django_db
def test_create_question_too_many_options_raises(user):
    """Больше 6-ти вариантов → ошибка"""
    service = CreateQuestionService()

    options = [
        {"text": f"Вариант {i}", "is_correct": (i == 1)}
        for i in range(1, 8)  # 7 вариантов
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )


@pytest.mark.django_db
def test_create_question_without_correct_option_raises(user):
    """Нет правильного ответа → ошибка"""
    service = CreateQuestionService()

    options = [
        {"text": "Ответ 1", "is_correct": False},
        {"text": "Ответ 2", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )


@pytest.mark.django_db
def test_create_question_with_multiple_correct_options_raises(user):
    """Несколько правильных ответов → ошибка"""
    service = CreateQuestionService()

    options = [
        {"text": "Ответ 1", "is_correct": True},
        {"text": "Ответ 2", "is_correct": True},
        {"text": "Ответ 3", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )


@pytest.mark.django_db
def test_create_question_with_empty_option_text_raises(user):
    """Пустой текст варианта (после strip) → ошибка"""
    service = CreateQuestionService()

    options = [
        {"text": "   ", "is_correct": True},
        {"text": "Нормальный ответ", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )


@pytest.mark.django_db
def test_create_question_with_too_long_option_text_raises(user):
    """Текст варианта > 300 символов → ошибка"""
    service = CreateQuestionService()

    long_text = "a" * 301

    options = [
        {"text": long_text, "is_correct": True},
        {"text": "Ещё один ответ", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        service.execute(
            author_id=user.id,
            text="Какой-то вопрос?",
            difficulty="easy",
            options=options,
        )
