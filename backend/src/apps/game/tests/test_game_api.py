# apps/game/tests/test_game_api.py

import pytest
from model_bakery import baker
from apps.rooms.models import Room, RoomParticipant
from apps.questions.models import Quiz, Question, AnswerOption
from apps.game.models import GameSession, GameRound, PlayerAnswer


@pytest.mark.django_db
def test_start_game_success(auth_client, user):
    room = baker.make(Room, host=user, status=Room.Status.OPEN)
    RoomParticipant.objects.create(room=room, user=user)

    q1 = baker.make(Question)
    q2 = baker.make(Question)
    quiz = baker.make(Quiz, author=user)
    quiz.questions.add(q1, through_defaults={"order": 1})
    quiz.questions.add(q2, through_defaults={"order": 2})

    res = auth_client.post(f"/api/game/rooms/{room.id}/start/", {
        "quiz_id": quiz.id
    })

    assert res.status_code == 201
    assert res.data["room"] == room.id
    assert res.data["quiz"] == quiz.id


@pytest.mark.django_db
def test_get_current_question(auth_client, user):
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz = baker.make(Quiz, author=user)
    question = baker.make(Question)
    quiz.questions.add(question, through_defaults={"order": 1})

    session = baker.make(GameSession, room=room, quiz=quiz, status=GameSession.Status.PLAYING)
    round1 = baker.make(GameRound, session=session, question=question, round_number=1, status=GameRound.Status.ACTIVE)

    res = auth_client.get(f"/api/game/sessions/{session.id}/current-question/")

    assert res.status_code == 200
    assert res.data["id"] == round1.id


@pytest.mark.django_db
def test_submit_answer_success(auth_client, user):
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    question = baker.make(Question, points=10)
    option_correct = baker.make(AnswerOption, question=question, is_correct=True)

    quiz = baker.make(Quiz, author=user)
    quiz.questions.add(question, through_defaults={"order": 1})

    session = baker.make(GameSession, room=room, quiz=quiz, status=GameSession.Status.PLAYING)
    round1 = baker.make(GameRound, session=session, question=question, round_number=1, status=GameRound.Status.ACTIVE)

    res = auth_client.post(
        f"/api/game/sessions/{session.id}/answer/",
        {"option_id": option_correct.id, "time_taken": 1.5}
    )

    assert res.status_code == 201
    assert res.data["is_correct"] is True
    assert res.data["points_earned"] > 0


@pytest.mark.django_db
def test_submit_answer_twice_error(auth_client, user):
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    question = baker.make(Question)
    option_correct = baker.make(AnswerOption, question=question, is_correct=True)

    quiz = baker.make(Quiz, author=user)
    quiz.questions.add(question, through_defaults={"order": 1})

    session = baker.make(GameSession, room=room, quiz=quiz, status=GameSession.Status.PLAYING)
    round1 = baker.make(GameRound, session=session, question=question, round_number=1, status=GameRound.Status.ACTIVE)

    # первый ответ
    PlayerAnswer.objects.create(
        round=round1, user=user, selected_option=option_correct,
        is_correct=True, time_taken=1.0
    )

    # второй ответ запрещён
    res = auth_client.post(
        f"/api/game/sessions/{session.id}/answer/",
        {"option_id": option_correct.id, "time_taken": 1.5}
    )

    assert res.status_code == 400


@pytest.mark.django_db
def test_my_game_sessions(auth_client, user):
    session1 = baker.make(GameSession)
    session2 = baker.make(GameSession)

    # привязка статистики
    session1.player_stats.create(user=user)
    session2.player_stats.create(user=user)

    res = auth_client.get("/api/game/sessions/my/")

    assert res.status_code == 200
    assert res.data["count"] == 2
