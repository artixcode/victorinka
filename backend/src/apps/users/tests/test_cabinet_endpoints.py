# apps/users/tests/test_cabinet_endpoints.py

import pytest
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.users.models import QuizBookmark, GameHistory
from apps.rooms.models import Room, RoomParticipant
from apps.game.models import GameSession
from apps.questions.models import Quiz

@pytest.mark.django_db
def test_my_bookmarks_list_returns_only_current_user(auth_client, user):
    User = get_user_model()

    # Викторины
    quiz1 = Quiz.objects.create(author=user, title="Quiz 1", status=Quiz.Status.PUBLISHED)
    quiz2 = Quiz.objects.create(author=user, title="Quiz 2", status=Quiz.Status.PUBLISHED)

    other = User.objects.create_user(
        email="other@example.com",
        password="12345test",
        nickname="other_nickname",
    )
    quiz3 = Quiz.objects.create(author=other, title="Quiz 3", status=Quiz.Status.PUBLISHED)

    # Закладки: две мои, одна чужая
    b1 = QuizBookmark.objects.create(user=user, quiz=quiz1, notes="mine1")
    b2 = QuizBookmark.objects.create(user=user, quiz=quiz3, notes="mine2")
    b_other = QuizBookmark.objects.create(user=other, quiz=quiz2, notes="other")

    res = auth_client.get("/api/cabinet/bookmarks/")

    assert res.status_code == 200

    # поддерживаем оба варианта: с пагинацией и без
    if isinstance(res.data, dict) and "results" in res.data:
        data = res.data["results"]
    else:
        data = res.data

    ids = [item["id"] for item in data]

    assert set(ids) == {b1.id, b2.id}
    assert b_other.id not in ids


@pytest.mark.django_db
def test_bookmark_create_success_for_published_quiz(auth_client, user):
    quiz = Quiz.objects.create(
        author=user,
        title="Published quiz",
        status=Quiz.Status.PUBLISHED,
    )

    payload = {"quiz": quiz.id, "notes": "interesting quiz"}
    res = auth_client.post("/api/cabinet/bookmarks/add/", payload, format="json")

    assert res.status_code == 201
    assert res.data["quiz"] == quiz.id
    assert QuizBookmark.objects.filter(user=user, quiz=quiz).exists()


@pytest.mark.django_db
def test_bookmark_create_fails_for_unpublished_quiz(auth_client, user):
    quiz = Quiz.objects.create(
        author=user,
        title="Draft quiz",
        status=Quiz.Status.DRAFT,
    )

    res = auth_client.post(
        "/api/cabinet/bookmarks/add/",
        {"quiz": quiz.id, "notes": "should fail"},
        format="json",
    )

    assert res.status_code == 400
    # ошибка должна быть привязана к полю quiz
    assert "quiz" in res.data


@pytest.mark.django_db
def test_bookmark_create_fails_for_duplicate(auth_client, user):
    quiz = Quiz.objects.create(
        author=user,
        title="Published quiz",
        status=Quiz.Status.PUBLISHED,
    )

    QuizBookmark.objects.create(user=user, quiz=quiz, notes="already")

    res = auth_client.post(
        "/api/cabinet/bookmarks/add/",
        {"quiz": quiz.id, "notes": "duplicate"},
        format="json",
    )

    assert res.status_code == 400
    assert "error" in res.data
    assert "уже в ваших закладках" in res.data["error"]


@pytest.mark.django_db
def test_bookmark_detail_get_patch_delete(auth_client, user):
    quiz = Quiz.objects.create(
        author=user,
        title="Bookmark quiz",
        status=Quiz.Status.PUBLISHED,
    )
    bookmark = QuizBookmark.objects.create(user=user, quiz=quiz, notes="initial")

    # GET
    res_get = auth_client.get(f"/api/cabinet/bookmarks/{bookmark.id}/")
    assert res_get.status_code == 200
    assert res_get.data["id"] == bookmark.id
    assert res_get.data["notes"] == "initial"

    # PATCH (обновление notes)
    res_patch = auth_client.patch(
        f"/api/cabinet/bookmarks/{bookmark.id}/",
        {"notes": "updated"},
        format="json",
    )
    assert res_patch.status_code == 200
    assert res_patch.data["notes"] == "updated"

    bookmark.refresh_from_db()
    assert bookmark.notes == "updated"

    # DELETE
    res_del = auth_client.delete(f"/api/cabinet/bookmarks/{bookmark.id}/")
    assert res_del.status_code == 204
    assert not QuizBookmark.objects.filter(id=bookmark.id).exists()


@pytest.mark.django_db
def test_my_game_history_returns_only_current_user_and_sorted(auth_client, user):
    User = get_user_model()
    now = timezone.now()

    # Комната и викторина
    room = Room.objects.create(
        name="Room 1",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="History quiz",
        status=Quiz.Status.PUBLISHED,
    )

    # Две сессии для текущего пользователя
    session1 = GameSession.objects.create(room=room, quiz=quiz)
    session2 = GameSession.objects.create(room=room, quiz=quiz)

    h1 = GameHistory.objects.create(
        user=user,
        session=session1,
        room=room,
        quiz=quiz,
        total_questions=10,
        correct_answers=7,
        final_points=100,
        played_at=now - timedelta(days=1),
    )
    h2 = GameHistory.objects.create(
        user=user,
        session=session2,
        room=room,
        quiz=quiz,
        total_questions=8,
        correct_answers=4,
        final_points=50,
        played_at=now,
    )

    # История другого пользователя (не должна попасть в ответ)
    other = User.objects.create_user(
        email="other2@example.com",
        password="12345test",
        nickname="other2",
    )
    other_room = Room.objects.create(
        name="Other room",
        host=other,
        status=Room.Status.FINISHED,
    )
    other_session = GameSession.objects.create(room=other_room, quiz=quiz)
    GameHistory.objects.create(
        user=other,
        session=other_session,
        room=other_room,
        quiz=quiz,
        total_questions=5,
        correct_answers=5,
        final_points=999,
        played_at=now,
    )

    res = auth_client.get("/api/cabinet/history/")

    assert res.status_code == 200

    # если включена пагинация, данные лежат в res.data["results"]
    if isinstance(res.data, dict) and "results" in res.data:
        data = res.data["results"]
    else:
        data = res.data

    assert len(data) == 2

    returned_ids = [item["id"] for item in data]
    # Должно быть отсортировано по -played_at: сначала h2, потом h1
    assert returned_ids == [h2.id, h1.id]

    # Проверяем, что accuracy сериализуется правильно (4/8*100 = 50.0)
    assert data[0]["accuracy"] == 50.0


@pytest.mark.django_db
def test_my_stats_view_returns_correct_counters(auth_client, user):
    User = get_user_model()

    # базовые поля пользователя
    user.total_points = 150
    user.total_wins = 3
    user.save(update_fields=["total_points", "total_wins"])

    # Комната + викторина
    room = Room.objects.create(
        name="Stats room",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="Stats quiz",
        status=Quiz.Status.PUBLISHED,
    )

    # Две сыгранные игры (history)
    session1 = GameSession.objects.create(room=room, quiz=quiz)
    session2 = GameSession.objects.create(room=room, quiz=quiz)

    GameHistory.objects.create(
        user=user,
        session=session1,
        room=room,
        quiz=quiz,
        total_questions=10,
        correct_answers=5,
    )
    GameHistory.objects.create(
        user=user,
        session=session2,
        room=room,
        quiz=quiz,
        total_questions=8,
        correct_answers=4,
    )

    # Закладки: 2 мои на РАЗНЫЕ викторины, одна чужая
    quiz2 = Quiz.objects.create(
        author=user,
        title="Stats quiz 2",
        status=Quiz.Status.PUBLISHED,
    )

    QuizBookmark.objects.create(user=user, quiz=quiz, notes="bk1")
    QuizBookmark.objects.create(user=user, quiz=quiz2, notes="bk2")

    other = User.objects.create_user(
        email="stats-other@example.com",
        password="12345test",
        nickname="stats_other",
    )
    other_quiz = Quiz.objects.create(
        author=other,
        title="Other quiz",
        status=Quiz.Status.PUBLISHED,
    )
    QuizBookmark.objects.create(user=other, quiz=other_quiz, notes="other")

    # Активные комнаты: 2 активные, 1 завершённая
    active_room1 = Room.objects.create(
        name="Active 1",
        host=user,
        status=Room.Status.OPEN,
    )
    active_room2 = Room.objects.create(
        name="Active 2",
        host=user,
        status=Room.Status.IN_PROGRESS,
    )
    finished_room = Room.objects.create(
        name="Finished",
        host=user,
        status=Room.Status.FINISHED,
    )

    RoomParticipant.objects.create(room=active_room1, user=user, role=RoomParticipant.Role.PLAYER)
    RoomParticipant.objects.create(room=active_room2, user=user, role=RoomParticipant.Role.PLAYER)
    RoomParticipant.objects.create(room=finished_room, user=user, role=RoomParticipant.Role.PLAYER)

    res = auth_client.get("/api/cabinet/stats/")

    assert res.status_code == 200
    data = res.data

    assert data["id"] == user.id
    assert data["total_points"] == 150
    assert data["total_wins"] == 3
    assert data["total_games"] == 2          # 2 GameHistory
    assert data["bookmarks_count"] == 2      # только его закладки
    assert data["active_rooms_count"] == 2   # только OPEN и IN_PROGRESS
