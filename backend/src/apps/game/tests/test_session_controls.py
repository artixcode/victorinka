import pytest
from rest_framework import status
from model_bakery import baker

from apps.rooms.models import Room, RoomParticipant
from apps.questions.models import Quiz, Question, AnswerOption, QuizQuestion
from apps.game.models import GameSession, GameRound


@pytest.mark.django_db
def create_quiz_with_one_question(user):
    """
    Создаём квиз с одним вопросом и двумя вариантами:
    - 1 правильный (order=1)
    - 1 неправильный (order=2)
    """
    quiz = baker.make(Quiz, author=user, status=Quiz.Status.PUBLISHED)

    question = baker.make(Question, author=user, points=10)

    # ВАЖНО: создаём варианты руками, чтобы не нарушать unique (question, order)
    opt1 = AnswerOption.objects.create(
        question=question,
        text="Correct",
        is_correct=True,
        order=1,
    )
    AnswerOption.objects.create(
        question=question,
        text="Wrong",
        is_correct=False,
        order=2,
    )

    QuizQuestion.objects.create(quiz=quiz, question=question, order=1)

    return quiz, question, opt1


@pytest.mark.django_db
def test_start_session_success(auth_client, user):
    """Хост успешно запускает игровую сессию"""

    # Комната и участник (хост)
    room = baker.make(Room, host=user, status=Room.Status.OPEN)
    RoomParticipant.objects.create(room=room, user=user)

    # Квиз с одним вопросом
    quiz, question, _ = create_quiz_with_one_question(user)

    # Сессия в статусе WAITING
    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.WAITING,
    )

    # Раунд в статусе WAITING
    round1 = GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.WAITING,
    )

    url = f"/api/game/sessions/{session.id}/start/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_200_OK

    session.refresh_from_db()
    round1.refresh_from_db()

    assert session.status == GameSession.Status.PLAYING
    assert round1.status == GameRound.Status.ACTIVE


@pytest.mark.django_db
def test_start_session_only_host(auth_client, user):
    """Только хост может запускать сессию"""

    room_host = baker.make("users.User")
    room = baker.make(Room, host=room_host, status=Room.Status.OPEN)

    # Пользователь — участник, но не хост
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, _ = create_quiz_with_one_question(room_host)

    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.WAITING,
    )

    url = f"/api/game/sessions/{session.id}/start/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "хост" in res.data["detail"].lower()


@pytest.mark.django_db
def test_pause_session(auth_client, user):
    """Пауза работает только когда игра идёт"""

    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, _, _ = create_quiz_with_one_question(user)

    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )

    url = f"/api/game/sessions/{session.id}/pause/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_200_OK
    session.refresh_from_db()
    assert session.status == GameSession.Status.PAUSED


@pytest.mark.django_db
def test_pause_session_only_host(auth_client, user):
    """Поставить на паузу может только хост"""

    host = baker.make("users.User")
    room = baker.make(Room, host=host, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, _, _ = create_quiz_with_one_question(host)

    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )

    url = f"/api/game/sessions/{session.id}/pause/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "хост" in res.data["detail"].lower()


@pytest.mark.django_db
def test_resume_session(auth_client, user):
    """Продолжение сессии работает только из статуса PAUSED"""

    room = baker.make(Room, host=user)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, _, _ = create_quiz_with_one_question(user)

    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PAUSED,
    )

    url = f"/api/game/sessions/{session.id}/resume/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_200_OK
    session.refresh_from_db()
    assert session.status == GameSession.Status.PLAYING


@pytest.mark.django_db
def test_resume_session_wrong_status(auth_client, user):
    """Если статус не PAUSED — возвращаем 400"""

    room = baker.make(Room, host=user)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, _, _ = create_quiz_with_one_question(user)

    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.WAITING,
    )

    url = f"/api/game/sessions/{session.id}/resume/"
    res = auth_client.post(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "невозможно продолжить" in res.data["error"].lower()
