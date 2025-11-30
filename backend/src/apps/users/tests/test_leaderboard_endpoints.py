import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import GameHistory
from apps.rooms.models import Room
from apps.game.models import GameSession
from apps.questions.models import Quiz


User = get_user_model()


def _get_paginated_data(response):
    """
    Вспомогалка: DRF ListAPIView (глобальный лидерборд) отдаёт пагинацию.
    Возвращаем именно список результатов.
    """
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data


# --------------------- GLOBAL LEADERBOARD ---------------------


@pytest.mark.django_db
def test_global_leaderboard_returns_active_users_with_games_sorted_by_points(auth_client, user):
    """
    /api/leaderboard/global/:
    - попадают только активные пользователи с играми
    - сортировка по -total_points по умолчанию
    - rank считается по количеству пользователей с большими total_points
    """
    # Приведём базового пользователя в понятное состояние
    user.nickname = "user_alpha"
    user.total_points = 100
    user.total_wins = 2
    user.save(update_fields=["nickname", "total_points", "total_wins"])

    # Ещё два пользователя
    u2 = User.objects.create_user(
        email="lb2@example.com",
        password="12345test",
        nickname="user_bravo",
    )
    u2.total_points = 200
    u2.total_wins = 5
    u2.save(update_fields=["total_points", "total_wins"])

    u3 = User.objects.create_user(
        email="lb3@example.com",
        password="12345test",
        nickname="user_charlie",
    )
    u3.total_points = 50
    u3.total_wins = 1
    u3.save(update_fields=["total_points", "total_wins"])

    # Одна общая комната и викторина
    room = Room.objects.create(
        name="LB Room",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="LB Quiz",
        status=Quiz.Status.PUBLISHED,
    )

    # Игровые сессии
    s1 = GameSession.objects.create(room=room, quiz=quiz)
    s2 = GameSession.objects.create(room=room, quiz=quiz)
    s3 = GameSession.objects.create(room=room, quiz=quiz)
    s4 = GameSession.objects.create(room=room, quiz=quiz)

    # История игр для каждого пользователя (чтобы они попали в leaderboard)
    GameHistory.objects.create(
        user=user,
        session=s1,
        room=room,
        quiz=quiz,
        final_points=60,
        correct_answers=7,
        total_questions=10,
    )
    GameHistory.objects.create(
        user=user,
        session=s2,
        room=room,
        quiz=quiz,
        final_points=40,
        correct_answers=3,
        total_questions=5,
    )

    GameHistory.objects.create(
        user=u2,
        session=s3,
        room=room,
        quiz=quiz,
        final_points=80,
        correct_answers=8,
        total_questions=10,
    )

    GameHistory.objects.create(
        user=u3,
        session=s4,
        room=room,
        quiz=quiz,
        final_points=30,
        correct_answers=4,
        total_questions=10,
    )

    # Запрос без параметров
    res = auth_client.get("/api/leaderboard/global/")
    assert res.status_code == 200

    data = _get_paginated_data(res)
    assert len(data) == 3

    # Проверяем порядок: u2 (200), user (100), u3 (50)
    nicknames = [item["nickname"] for item in data]
    assert nicknames == ["user_bravo", "user_alpha", "user_charlie"]

    # Проверяем ранги (по total_points)
    ranks = {item["nickname"]: item["rank"] for item in data}
    assert ranks["user_bravo"] == 1  # у него больше всех очков
    assert ranks["user_alpha"] == 2
    assert ranks["user_charlie"] == 3

    # Проверяем total_games через сериализатор
    games = {item["nickname"]: item["total_games"] for item in data}
    assert games["user_alpha"] == 2
    assert games["user_bravo"] == 1
    assert games["user_charlie"] == 1

    # То же самое, но с limit=2
    res_limit = auth_client.get("/api/leaderboard/global/?limit=2")
    assert res_limit.status_code == 200
    data_limit = _get_paginated_data(res_limit)
    assert len(data_limit) == 2
    nicknames_limit = [item["nickname"] for item in data_limit]
    assert nicknames_limit == ["user_bravo", "user_alpha"]


# --------------------- QUIZ LEADERBOARD ---------------------


@pytest.mark.django_db
def test_quiz_leaderboard_returns_best_scores_and_avg_accuracy(auth_client, user):
    """
    /api/leaderboard/quiz/<quiz_id>/:
    Проверяем:
    - агрегацию best_score, games_played, avg_accuracy
    - сортировку по -best_score, -avg_accuracy
    """
    user.nickname = "quiz_user1"
    user.save(update_fields=["nickname"])

    u2 = User.objects.create_user(
        email="quiz2@example.com",
        password="12345test",
        nickname="quiz_user2",
    )

    room = Room.objects.create(
        name="Quiz Room",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="Quiz LB",
        status=Quiz.Status.PUBLISHED,
    )

    # Сессии
    s1 = GameSession.objects.create(room=room, quiz=quiz)
    s2 = GameSession.objects.create(room=room, quiz=quiz)
    s3 = GameSession.objects.create(room=room, quiz=quiz)
    s4 = GameSession.objects.create(room=room, quiz=quiz)

    # user: две игры, лучший балл 100, средняя точность 85%
    GameHistory.objects.create(
        user=user,
        session=s1,
        room=room,
        quiz=quiz,
        final_points=100,
        correct_answers=9,
        total_questions=10,
    )
    GameHistory.objects.create(
        user=user,
        session=s2,
        room=room,
        quiz=quiz,
        final_points=80,
        correct_answers=8,
        total_questions=10,
    )

    # u2: две игры, лучший балл 90, средняя точность 70%
    GameHistory.objects.create(
        user=u2,
        session=s3,
        room=room,
        quiz=quiz,
        final_points=90,
        correct_answers=7,
        total_questions=10,
    )
    GameHistory.objects.create(
        user=u2,
        session=s4,
        room=room,
        quiz=quiz,
        final_points=70,
        correct_answers=7,
        total_questions=10,
    )

    res = auth_client.get(f"/api/leaderboard/quiz/{quiz.id}/")
    assert res.status_code == 200

    assert res.data["quiz_id"] == quiz.id
    assert res.data["quiz_title"] == quiz.title

    leaderboard = res.data["leaderboard"]
    assert len(leaderboard) == 2

    # Первый должен быть user с best_score=100
    first = leaderboard[0]
    second = leaderboard[1]

    assert first["user_id"] == user.id
    assert first["best_score"] == 100
    assert first["games_played"] == 2
    assert first["avg_accuracy"] == 85.0  # (9+8)/2/10 * 100

    assert second["user_id"] == u2.id
    assert second["best_score"] == 90
    assert second["games_played"] == 2
    assert second["avg_accuracy"] == 70.0  # (7+7)/2/10 * 100


# --------------------- ROOM LEADERBOARD ---------------------


@pytest.mark.django_db
def test_room_leaderboard_orders_by_best_score_then_avg_rank(auth_client, user):
    """
    /api/leaderboard/room/<room_id>/:
    Текущее поведение:
    - сортировка по best_score (убывание),
      при равенстве — по avg_rank (возрастание).
    - проверяем поля best_score, games_played, avg_rank, best_rank
    """
    user.nickname = "room_user1"
    user.save(update_fields=["nickname"])

    u2 = User.objects.create_user(
        email="room2@example.com",
        password="12345test",
        nickname="room_user2",
    )

    room = Room.objects.create(
        name="Room LB",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="Room Quiz",
        status=Quiz.Status.PUBLISHED,
    )

    # Сессии
    s1 = GameSession.objects.create(room=room, quiz=quiz)
    s2 = GameSession.objects.create(room=room, quiz=quiz)
    s3 = GameSession.objects.create(room=room, quiz=quiz)
    s4 = GameSession.objects.create(room=room, quiz=quiz)

    # user: avg_rank = 2.0, best_score = 100
    GameHistory.objects.create(
        user=user,
        session=s1,
        room=room,
        quiz=quiz,
        final_points=100,
        correct_answers=8,
        total_questions=10,
        final_rank=2,
    )
    GameHistory.objects.create(
        user=user,
        session=s2,
        room=room,
        quiz=quiz,
        final_points=80,
        correct_answers=7,
        total_questions=10,
        final_rank=2,
    )

    # u2: avg_rank = 1.5, best_score = 95
    GameHistory.objects.create(
        user=u2,
        session=s3,
        room=room,
        quiz=quiz,
        final_points=95,
        correct_answers=9,
        total_questions=10,
        final_rank=1,
    )
    GameHistory.objects.create(
        user=u2,
        session=s4,
        room=room,
        quiz=quiz,
        final_points=85,
        correct_answers=8,
        total_questions=10,
        final_rank=2,
    )

    res = auth_client.get(f"/api/leaderboard/room/{room.id}/")
    assert res.status_code == 200

    assert res.data["room_id"] == room.id
    assert res.data["room_name"] == room.name

    leaderboard = res.data["leaderboard"]
    assert len(leaderboard) == 2

    first = leaderboard[0]
    second = leaderboard[1]

    # Сейчас первым идёт тот, у кого лучший best_score (user)
    assert first["user_id"] == user.id
    assert first["best_score"] == 100
    assert first["games_played"] == 2
    assert first["avg_rank"] == 2.0
    assert first["best_rank"] == 2

    # Второй — u2 с меньшим best_score, но лучшим avg_rank
    assert second["user_id"] == u2.id
    assert second["best_score"] == 95
    assert second["games_played"] == 2
    assert second["avg_rank"] == 1.5
    assert second["best_rank"] == 1


# --------------------- USER STATS DETAIL ---------------------


@pytest.mark.django_db
def test_user_stats_detail_for_self_includes_email_and_correct_stats(auth_client, user):
    """
    /api/leaderboard/user/<user_id>/:
    - для самого себя email виден
    - считаются total_games, avg_accuracy, best_game_points, global_rank
    """
    user.total_points = 150
    user.total_wins = 3
    user.save(update_fields=["total_points", "total_wins"])

    # Пользователь с бОльшими очками, влияет на global_rank
    richer = User.objects.create_user(
        email="rich@example.com",
        password="12345test",
        nickname="rich_user",
    )
    richer.total_points = 300
    richer.save(update_fields=["total_points"])

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

    s1 = GameSession.objects.create(room=room, quiz=quiz)
    s2 = GameSession.objects.create(room=room, quiz=quiz)

    # Две игры: avg_accuracy = 60.0, best_game_points = 100
    GameHistory.objects.create(
        user=user,
        session=s1,
        room=room,
        quiz=quiz,
        final_points=100,
        correct_answers=8,
        total_questions=10,
    )
    GameHistory.objects.create(
        user=user,
        session=s2,
        room=room,
        quiz=quiz,
        final_points=50,
        correct_answers=4,
        total_questions=10,
    )

    res = auth_client.get(f"/api/leaderboard/user/{user.id}/")
    assert res.status_code == 200

    data = res.data

    assert data["user_id"] == user.id
    assert data["nickname"] == user.nickname
    # для самого себя email должен быть виден
    assert data["email"] == user.email

    assert data["total_games"] == 2
    assert data["avg_accuracy"] == 60.0    # ((8+4)/2)/10*100
    assert data["best_game_points"] == 100
    # один пользователь богаче по очкам → ранг 2
    assert data["global_rank"] == 2


@pytest.mark.django_db
def test_user_stats_detail_for_other_user_hides_email(auth_client, user):
    """
    /api/leaderboard/user/<user_id>/:
    если запрашиваем ЧУЖОГО пользователя и мы не staff — email должен быть скрыт
    """
    other = User.objects.create_user(
        email="other_stats@example.com",
        password="12345test",
        nickname="other_stats",
    )

    room = Room.objects.create(
        name="Other stats room",
        host=other,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=other,
        title="Other stats quiz",
        status=Quiz.Status.PUBLISHED,
    )
    session = GameSession.objects.create(room=room, quiz=quiz)

    GameHistory.objects.create(
        user=other,
        session=session,
        room=room,
        quiz=quiz,
        final_points=70,
        correct_answers=7,
        total_questions=10,
    )

    res = auth_client.get(f"/api/leaderboard/user/{other.id}/")
    assert res.status_code == 200

    data = res.data
    assert data["user_id"] == other.id
    # мы залогинены как fixture user, а не как other, и не staff → email скрыт
    assert data["email"] is None
