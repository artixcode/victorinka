import pytest
from model_bakery import baker
from django.urls import reverse
from django.utils import timezone

from apps.rooms.models import Room, RoomParticipant
from apps.questions.models import Quiz, Question, AnswerOption, QuizQuestion
from apps.game.models import GameSession, GameRound, PlayerAnswer


@pytest.mark.django_db
def create_quiz_with_questions(author, count=2):
    """
    Создаёт валидный опубликованный quiz с count вопросами.
    """
    quiz = baker.make(
        Quiz,
        author=author,
        status=Quiz.Status.PUBLISHED,
        visibility=Quiz.Visibility.PUBLIC,
    )

    questions = []
    for i in range(count):
        q = baker.make(
            Question,
            author=author,
            points=10,
            text=f"Question {i}",
        )
        # Один правильный и один неправильный вариант
        AnswerOption.objects.create(question=q, text="Correct", is_correct=True, order=1)
        AnswerOption.objects.create(question=q, text="Wrong", is_correct=False, order=2)
        questions.append(q)

    for idx, q in enumerate(questions, start=1):
        QuizQuestion.objects.create(
            quiz=quiz,
            question=q,
            order=idx
        )

    return quiz, questions


@pytest.mark.django_db
def create_room_with_participants(host, participants=None, status=Room.Status.OPEN):
    """
    Создаёт комнату и добавляет участников.
    """
    room = baker.make(Room, host=host, status=status)

    RoomParticipant.objects.create(room=room, user=host, role=RoomParticipant.Role.HOST)

    if participants:
        for user in participants:
            RoomParticipant.objects.create(room=room, user=user)

    return room


# ----------------------------
#        TESTS
# ----------------------------


@pytest.mark.django_db
def test_start_game_success(auth_client, user):
    """
    Проверяем успешный запуск игры.
    """
    p2 = baker.make("users.User")

    room = create_room_with_participants(host=user, participants=[p2])

    quiz, questions = create_quiz_with_questions(author=user, count=2)

    url = f"/api/game/rooms/{room.id}/start/"

    res = auth_client.post(url, {"quiz_id": quiz.id}, format="json")

    assert res.status_code == 201
    assert res.data["quiz"] == quiz.id
    assert res.data["room"] == room.id

    session = GameSession.objects.get(id=res.data["id"])

    rounds = session.rounds.order_by("round_number")
    assert rounds.count() == 2
    assert rounds.first().question == questions[0]


@pytest.mark.django_db
def test_start_game_not_host(auth_client, user):
    """
    Нельзя запустить игру, если не хост.
    """
    stranger = baker.make("users.User")

    room = create_room_with_participants(host=stranger)

    quiz, _ = create_quiz_with_questions(author=stranger)

    url = f"/api/game/rooms/{room.id}/start/"

    res = auth_client.post(url, {"quiz_id": quiz.id}, format="json")

    assert res.status_code == 403
    assert "Только хост" in res.data["detail"]


@pytest.mark.django_db
def test_submit_answer_success(auth_client, user):
    """
    Корректная отправка ответа.
    """
    p2 = baker.make("users.User")

    room = create_room_with_participants(host=user, participants=[p2])
    quiz, questions = create_quiz_with_questions(author=user, count=1)

    session = baker.make(GameSession, room=room, quiz=quiz, status=GameSession.Status.PLAYING)
    round1 = baker.make(
        GameRound,
        session=session,
        question=questions[0],
        round_number=1,
        status=GameRound.Status.ACTIVE,
        started_at=timezone.now()
    )

    correct_option = questions[0].options.get(is_correct=True)

    url = f"/api/game/sessions/{session.id}/answer/"

    res = auth_client.post(url, {"selected_option": correct_option.id}, format="json")

    assert res.status_code == 201
    assert res.data["is_correct"] is True
    assert res.data["points_earned"] > 0

@pytest.mark.django_db
def test_submit_answer_twice(auth_client, user):
    """
    Повторная отправка ответа должна выдавать ошибку
    при активной игре (уже ответили).
    """
    p2 = baker.make("users.User")

    room = create_room_with_participants(host=user, participants=[p2])
    quiz, questions = create_quiz_with_questions(author=user, count=1)

    session = baker.make(GameSession, room=room, quiz=quiz, status=GameSession.Status.PLAYING)
    round1 = baker.make(
        GameRound,
        session=session,
        question=questions[0],
        round_number=1,
        started_at=timezone.now(),
        status=GameRound.Status.ACTIVE,
    )

    opt = questions[0].options.first()

    baker.make("game.PlayerGameStats", session=session, user=user)
    baker.make("game.PlayerGameStats", session=session, user=p2)

    url = f"/api/game/sessions/{session.id}/answer/"

    auth_client.post(url, {"selected_option": opt.id}, format="json")

    res2 = auth_client.post(url, {"selected_option": opt.id}, format="json")

    assert res2.status_code == 400
    assert "уже" in res2.data["error"].lower()


@pytest.mark.django_db
def test_my_game_sessions(auth_client, user):
    room = create_room_with_participants(host=user)
    quiz, _ = create_quiz_with_questions(author=user, count=1)

    # моя сессия
    session1 = baker.make(GameSession, room=room, quiz=quiz)
    baker.make("game.PlayerGameStats", session=session1, user=user)

    # чужая сессия
    stranger = baker.make("users.User")
    room2 = create_room_with_participants(host=stranger)
    session2 = baker.make(GameSession, room=room2, quiz=quiz)
    baker.make("game.PlayerGameStats", session=session2, user=stranger)

    res = auth_client.get("/api/game/sessions/my/")

    assert res.status_code == 200
    assert "results" in res.data

    ids = [s["id"] for s in res.data["results"]]

    assert session1.id in ids
    assert session2.id not in ids
