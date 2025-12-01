import pytest
from django.utils import timezone
from rest_framework import status
from model_bakery import baker

from apps.rooms.models import Room, RoomParticipant
from apps.game.models import GameSession, GameRound, PlayerGameStats
from test_session_controls import create_quiz_with_one_question

@pytest.mark.django_db
def test_get_current_question_success(auth_client, user):
    """
    Участник игры успешно получает текущий вопрос.
    """
    # Хост = текущий пользователь
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, _ = create_quiz_with_one_question(user)

    # Сессия уже в статусе PLAYING, текущий индекс = 0 (первый вопрос)
    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
        current_question_index=0,
    )

    # Раунд для этого вопроса
    round1 = GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.ACTIVE,
        started_at=timezone.now(),
    )

    url = f"/api/game/sessions/{session.id}/current-question/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    # Проверяем, что вернулся именно наш раунд
    assert res.data["id"] == round1.id
    assert res.data["question"] == question.id
    # Убедимся, что вложенные данные вопроса тоже есть
    assert res.data["question_data"]["id"] == question.id


@pytest.mark.django_db
def test_get_current_question_wrong_status(auth_client, user):
    """
    Если игра не в статусе PLAYING/PAUSED — возвращаем 400 и ошибку "Игра не идёт".
    """
    room = baker.make(Room, host=user, status=Room.Status.OPEN)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, _ = create_quiz_with_one_question(user)

    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.WAITING,
        current_question_index=0,
    )

    GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.WAITING,
    )

    url = f"/api/game/sessions/{session.id}/current-question/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "игра не идёт" in res.data["error"].lower()


@pytest.mark.django_db
def test_get_current_question_no_round(auth_client, user):
    """
    Если подходящий раунд не найден — 404 и "Текущий раунд не найден".
    """
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, _ = create_quiz_with_one_question(user)

    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
        current_question_index=1,
    )

    GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.ACTIVE,
    )

    url = f"/api/game/sessions/{session.id}/current-question/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "текущий раунд не найден" in res.data["error"].lower()


@pytest.mark.django_db
def test_get_current_question_not_participant(auth_client, user):
    """
    Если пользователь не участник комнаты — 403.
    """
    host = baker.make("users.User")
    room = baker.make(Room, host=host, status=Room.Status.IN_PROGRESS)

    quiz, question, _ = create_quiz_with_one_question(host)

    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
        current_question_index=0,
    )

    GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.ACTIVE,
    )

    url = f"/api/game/sessions/{session.id}/current-question/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "не являетесь участником" in res.data["detail"].lower()

@pytest.mark.django_db
def test_get_results_success(auth_client, user):
    """
    Участник может получить результаты завершённой игры.
    """
    room = baker.make(Room, host=user, status=Room.Status.FINISHED)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, _ = create_quiz_with_one_question(user)

    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.FINISHED,
        current_question_index=0,
        started_at=timezone.now(),
        finished_at=timezone.now(),
    )

    # Один завершённый раунд
    GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.COMPLETED,
        started_at=timezone.now(),
        completed_at=timezone.now(),
    )

    # Статистика игрока
    stats = PlayerGameStats.objects.create(
        session=session,
        user=user,
        total_points=25,
        correct_answers=2,
        wrong_answers=0,
        rank=1,
        completed_at=timezone.now(),
    )

    url = f"/api/game/sessions/{session.id}/results/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK

    assert "session" in res.data
    assert "leaderboard" in res.data
    assert "total_rounds" in res.data
    assert "completed_rounds" in res.data

    assert res.data["total_rounds"] == 1
    assert res.data["completed_rounds"] == 1

    assert isinstance(res.data["leaderboard"], list)
    assert len(res.data["leaderboard"]) == 1

    lb_item = res.data["leaderboard"][0]
    assert lb_item["user"] == user.id
    assert lb_item["total_points"] == stats.total_points
    assert lb_item["correct_answers"] == stats.correct_answers
    assert lb_item["rank"] == stats.rank


@pytest.mark.django_db
def test_get_results_not_participant(auth_client, user):
    """
    Не-участник не может смотреть результаты игры — 403.
    """
    host = baker.make("users.User")
    room = baker.make(Room, host=host, status=Room.Status.FINISHED)

    quiz, question, _ = create_quiz_with_one_question(host)

    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.FINISHED,
    )

    GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.COMPLETED,
    )

    url = f"/api/game/sessions/{session.id}/results/"
    res = auth_client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "не являетесь участником" in res.data["detail"].lower()
