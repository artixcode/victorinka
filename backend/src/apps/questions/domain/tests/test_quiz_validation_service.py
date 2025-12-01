import pytest
from apps.questions.domain.services.quiz_validation_service import (
    QuizValidationService,
    QuizValidationException,
)
from apps.questions.models import Quiz, Question, AnswerOption, QuizQuestion


def _create_valid_question(author, idx: int, points: int = 5) -> Question:
    """Хелпер: создаёт валидный вопрос с 2 вариантами, один правильный."""
    question = Question.objects.create(
        author=author,
        text=f"Вопрос {idx}?",
        difficulty=Question.Difficulty.EASY,
        points=points,
    )

    # два варианта, первый правильный
    opt1 = AnswerOption.objects.create(
        question=question,
        text="Вариант 1",
        is_correct=True,
        order=1,
    )
    AnswerOption.objects.create(
        question=question,
        text="Вариант 2",
        is_correct=False,
        order  =2,
    )

    return question


@pytest.mark.django_db
def test_valid_quiz_can_be_published(user):
    """Корректная викторина проходит валидацию без ошибок."""
    quiz = Quiz.objects.create(
        author=user,
        title="Моя викторина",
    )

    # Минимум 5 вопросов
    for i in range(1, 6):
        q = _create_valid_question(user, i)
        QuizQuestion.objects.create(quiz=quiz, question=q, order=i)

    service = QuizValidationService()

    is_valid, errors = service.validate_for_publication(quiz)

    assert is_valid is True
    assert errors == []
    assert service.can_publish(quiz) is True


@pytest.mark.django_db
def test_quiz_with_too_few_questions_invalid(user):
    """Меньше 5 вопросов -> валидация проваливается."""
    quiz = Quiz.objects.create(
        author=user,
        title="Короткая викторина",
    )

    for i in range(1, 3):  # только 2 вопроса
        q = _create_valid_question(user, i)
        QuizQuestion.objects.create(quiz=quiz, question=q, order=i)

    service = QuizValidationService()

    is_valid, errors = service.validate_for_publication(quiz)

    assert is_valid is False
    assert any("Недостаточно вопросов" in e for e in errors)


@pytest.mark.django_db
def test_question_without_correct_option_produces_error(user):
    """Вопрос без правильного ответа -> ошибка для конкретного вопроса."""
    quiz = Quiz.objects.create(
        author=user,
        title="Викторина с ошибкой",
    )

    # 1) Невалидный вопрос: без правильного ответа
    bad_question = Question.objects.create(
        author=user,
        text="Плохой вопрос?",
        difficulty=Question.Difficulty.EASY,
        points=5,
    )
    AnswerOption.objects.create(
        question=bad_question,
        text="Вариант 1",
        is_correct=False,
        order=1,
    )
    AnswerOption.objects.create(
        question=bad_question,
        text="Вариант 2",
        is_correct=False,
        order=2,
    )
    QuizQuestion.objects.create(quiz=quiz, question=bad_question, order=1)

    # 2) Остальные вопросы валидные
    for i in range(2, 6):
        q = _create_valid_question(user, i)
        QuizQuestion.objects.create(quiz=quiz, question=q, order=i)

    service = QuizValidationService()

    is_valid, errors = service.validate_for_publication(quiz)

    assert is_valid is False
    assert any("нет правильного ответа" in e for e in errors)


@pytest.mark.django_db
def test_question_with_too_few_options_produces_error(user):
    """Вопрос с 1 вариантом -> ошибка по количеству вариантов."""
    quiz = Quiz.objects.create(
        author=user,
        title="Викторина с малым числом вариантов",
    )

    # Плохой вопрос: только один вариант
    q_bad = Question.objects.create(
        author=user,
        text="Вопрос с 1 вариантом?",
        difficulty=Question.Difficulty.EASY,
        points=5,
    )
    AnswerOption.objects.create(
        question=q_bad,
        text="Один вариант",
        is_correct=True,
        order=1,
    )
    QuizQuestion.objects.create(quiz=quiz, question=q_bad, order=1)

    # Остальные валидные
    for i in range(2, 6):
        q = _create_valid_question(user, i)
        QuizQuestion.objects.create(quiz=quiz, question=q, order=i)

    service = QuizValidationService()
    is_valid, errors = service.validate_for_publication(quiz)

    assert is_valid is False
    assert any("недостаточно вариантов ответа" in e for e in errors)


@pytest.mark.django_db
def test_question_with_zero_points_produces_error(user):
    """Вопрос с 0 очков -> ошибка."""
    quiz = Quiz.objects.create(
        author=user,
        title="Викторина с неверными очками",
    )

    # Плохой вопрос: 0 очков
    q_bad = _create_valid_question(user, idx=1, points=0)
    QuizQuestion.objects.create(quiz=quiz, question=q_bad, order=1)

    # Остальные нормальные
    for i in range(2, 6):
        q = _create_valid_question(user, i)
        QuizQuestion.objects.create(quiz=quiz, question=q, order=i)

    service = QuizValidationService()
    is_valid, errors = service.validate_for_publication(quiz)

    assert is_valid is False
    assert any("очки должны быть больше 0" in e for e in errors)


@pytest.mark.django_db
def test_validate_or_raise_raises_exception_for_invalid_quiz(user):
    """validate_or_raise бросает QuizValidationException при ошибке."""
    quiz = Quiz.objects.create(
        author=user,
        title="Слишком короткая викторина",
    )
    # всего один валидный вопрос — недостаточно по MIN_QUESTIONS
    q = _create_valid_question(user, 1)
    QuizQuestion.objects.create(quiz=quiz, question=q, order=1)

    service = QuizValidationService()

    with pytest.raises(QuizValidationException):
        service.validate_or_raise(quiz)
