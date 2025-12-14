import types

import pytest
from model_bakery import baker

from apps.game.permissions import (
    IsRoomHost,
    IsGameParticipant,
    CanAnswerQuestion,
)
from apps.rooms.models import Room, RoomParticipant
from apps.game.models import GameSession, GameRound, PlayerAnswer
from apps.questions.models import Quiz, Question, AnswerOption, QuizQuestion


def create_quiz_with_one_question_for_permissions(user):
    """
    Мини-хелпер (упрощённая версия из test_session_controls):
    квиз с 1 вопросом и 2 вариантами.
    """
    quiz = baker.make(Quiz, author=user, status=Quiz.Status.PUBLISHED)
    question = baker.make(Question, author=user, points=10)

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


# ---------- IsRoomHost ----------

@pytest.mark.django_db
def test_is_room_host_true_for_room_host(user):
    """IsRoomHost: объект с полем host, текущий пользователь — хост."""
    room = baker.make(Room, host=user)

    request = types.SimpleNamespace(user=user)
    perm = IsRoomHost()

    assert perm.has_object_permission(request, None, room) is True


@pytest.mark.django_db
def test_is_room_host_false_for_non_host(user):
    """IsRoomHost: текущий пользователь НЕ хост комнаты."""
    other = baker.make("users.User", nickname="other_user")
    room = baker.make(Room, host=other)

    request = types.SimpleNamespace(user=user)
    perm = IsRoomHost()

    assert perm.has_object_permission(request, None, room) is False


@pytest.mark.django_db
def test_is_room_host_true_for_object_with_room_field(user):
    """IsRoomHost: объект без host, но с room.host == user."""
    room = baker.make(Room, host=user)
    # GameSession имеет поле room
    quiz = baker.make(Quiz, author=user, status=Quiz.Status.PUBLISHED)
    session = baker.make(GameSession, room=room, quiz=quiz)

    request = types.SimpleNamespace(user=user)
    perm = IsRoomHost()

    assert perm.has_object_permission(request, None, session) is True


@pytest.mark.django_db
def test_is_room_host_false_when_object_has_no_host_or_room(user):
    """IsRoomHost: объект без host и room -> False."""
    obj = types.SimpleNamespace()  # пустой объект

    request = types.SimpleNamespace(user=user)
    perm = IsRoomHost()

    assert perm.has_object_permission(request, None, obj) is False


# ---------- IsGameParticipant ----------

@pytest.mark.django_db
def test_is_game_participant_for_room_object_returns_false(user):
    """
    IsGameParticipant: для объекта Room permission не срабатывает,
    даже если пользователь участвует в комнате.
    Permission рассчитан на GameSession / GameRound.
    """
    room = baker.make(Room, host=user)
    RoomParticipant.objects.create(room=room, user=user)

    request = types.SimpleNamespace(user=user)
    perm = IsGameParticipant()

    assert perm.has_object_permission(request, None, room) is False



@pytest.mark.django_db
def test_is_game_participant_true_for_session_object(user):
    """IsGameParticipant: пользователь участвует в комнате (obj = GameSession)."""
    room = baker.make(Room, host=user)
    RoomParticipant.objects.create(room=room, user=user)

    quiz = baker.make(Quiz, author=user, status=Quiz.Status.PUBLISHED)
    session = baker.make(GameSession, room=room, quiz=quiz)

    request = types.SimpleNamespace(user=user)
    perm = IsGameParticipant()

    assert perm.has_object_permission(request, None, session) is True


@pytest.mark.django_db
def test_is_game_participant_false_for_non_participant(user):
    """IsGameParticipant: пользователь НЕ участник комнаты."""
    room = baker.make(Room, host=user)
    # участников не создаём

    request = types.SimpleNamespace(user=user)
    perm = IsGameParticipant()

    assert perm.has_object_permission(request, None, room) is False


@pytest.mark.django_db
def test_is_game_participant_false_when_object_has_no_room_or_session(user):
    """IsGameParticipant: объект без room/session -> False."""
    obj = types.SimpleNamespace()

    request = types.SimpleNamespace(user=user)
    perm = IsGameParticipant()

    assert perm.has_object_permission(request, None, obj) is False


# ---------- CanAnswerQuestion ----------

@pytest.mark.django_db
def test_can_answer_question_success(user):
    """
    CanAnswerQuestion:
    - раунд ACTIVE
    - пользователь участник комнаты
    - ещё не отвечал
    """
    quiz, question, correct_option = create_quiz_with_one_question_for_permissions(user)
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )
    game_round = baker.make(
        GameRound,
        session=session,
        question=question,
        status=GameRound.Status.ACTIVE,
    )

    RoomParticipant.objects.create(room=room, user=user)

    request = types.SimpleNamespace(user=user)
    perm = CanAnswerQuestion()

    assert perm.has_object_permission(request, None, game_round) is True


@pytest.mark.django_db
def test_can_answer_question_fails_when_round_not_active(user):
    """CanAnswerQuestion: раунд не активен -> False, message про «Раунд не активен»."""
    quiz, question, _ = create_quiz_with_one_question_for_permissions(user)
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )
    game_round = baker.make(
        GameRound,
        session=session,
        question=question,
        status=GameRound.Status.WAITING,
    )

    RoomParticipant.objects.create(room=room, user=user)

    request = types.SimpleNamespace(user=user)
    perm = CanAnswerQuestion()

    assert perm.has_object_permission(request, None, game_round) is False
    assert "Раунд не активен" in perm.message


@pytest.mark.django_db
def test_can_answer_question_fails_when_user_not_participant(user):
    """CanAnswerQuestion: пользователь не в participants комнаты."""
    quiz, question, _ = create_quiz_with_one_question_for_permissions(user)
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )
    game_round = baker.make(
        GameRound,
        session=session,
        question=question,
        status=GameRound.Status.ACTIVE,
    )

    # участников не создаём
    request = types.SimpleNamespace(user=user)
    perm = CanAnswerQuestion()

    assert perm.has_object_permission(request, None, game_round) is False
    assert "не являетесь участником" in perm.message


@pytest.mark.django_db
def test_can_answer_question_fails_when_user_already_answered(user):
    """CanAnswerQuestion: пользователь уже ответил на вопрос."""
    quiz, question, correct_option = create_quiz_with_one_question_for_permissions(user)
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    session = baker.make(
        GameSession,
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
    )
    game_round = baker.make(
        GameRound,
        session=session,
        question=question,
        status=GameRound.Status.ACTIVE,
    )

    # пользователь участвует
    RoomParticipant.objects.create(room=room, user=user)

    # и уже есть ответ от этого пользователя
    baker.make(
        PlayerAnswer,
        round=game_round,
        user=user,
        selected_option=correct_option,
        is_correct=True,
    )

    request = types.SimpleNamespace(user=user)
    perm = CanAnswerQuestion()

    assert perm.has_object_permission(request, None, game_round) is False
    assert "уже ответили" in perm.message
