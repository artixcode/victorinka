import pytest
from django.utils import timezone
from rest_framework import status

from model_bakery import baker

from apps.rooms.models import Room, RoomParticipant
from apps.game.models import GameSession, GameRound, PlayerGameStats
from apps.questions.models import Quiz, Question, AnswerOption, QuizQuestion
from apps.users.models import GameHistory


def create_single_question_quiz(author):
    """
    Утилита: создает опубликованную викторину с одним вопросом и двумя вариантами ответов.
    Возвращает (quiz, question, correct_option).
    """

    question = Question.objects.create(
        author=author,
        text="Test question?",
        explanation="",
        difficulty=Question.Difficulty.MEDIUM,
        points=10,
    )

    correct_opt = AnswerOption.objects.create(
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

    quiz = Quiz.objects.create(
        author=author,
        title="Single question quiz",
        description="",
        status=Quiz.Status.PUBLISHED,
    )

    # Связка через through-модель
    QuizQuestion.objects.create(
        quiz=quiz,
        question=question,
        order=1,
    )

    return quiz, question, correct_opt


@pytest.mark.django_db
def test_finish_game_after_last_answer(auth_client, user):
    """
    Проверяем, что при ответе на последний вопрос:
    - сессия переходит в статус FINISHED
    - раунд становится COMPLETED
    - создаётся PlayerGameStats с правильными данными и rank=1
    - создаётся запись в GameHistory
    - в ответе API флаги game_finished/next_question выставлены корректно
    """
    room = baker.make(Room, host=user, status=Room.Status.IN_PROGRESS)
    RoomParticipant.objects.create(room=room, user=user)

    quiz, question, correct_opt = create_single_question_quiz(user)

    # Сессия в статусе PLAYING, на первом вопросе
    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
        status=GameSession.Status.PLAYING,
        current_question_index=0,
        started_at=timezone.now(),
    )

    game_round = GameRound.objects.create(
        session=session,
        question=question,
        round_number=1,
        time_limit=30,
        status=GameRound.Status.ACTIVE,
        started_at=timezone.now(),
    )

    url = f"/api/game/sessions/{session.id}/answer/"

    res = auth_client.post(url, {"selected_option": correct_opt.id}, format="json")

    assert res.status_code == status.HTTP_201_CREATED

    data = res.data
    # Проверяем флаги в ответе API
    assert data["game_finished"] is True
    assert data["next_question"] is False
    assert data["is_correct"] is True
    assert data["points_earned"] >= question.points

    # Обновляем объекты из БД
    session.refresh_from_db()
    game_round.refresh_from_db()

    # Сессия должна быть завершена
    assert session.status == GameSession.Status.FINISHED
    assert session.finished_at is not None

    # Раунд завершён
    assert game_round.status == GameRound.Status.COMPLETED
    assert game_round.completed_at is not None

    # Статистика игрока
    stats = PlayerGameStats.objects.get(session=session, user=user)
    assert stats.total_points == data["points_earned"]
    assert stats.correct_answers == 1
    assert stats.wrong_answers == 0
    assert stats.rank == 1
    assert stats.completed_at is not None

    # История игр
    history_qs = GameHistory.objects.filter(session=session, user=user)
    assert history_qs.count() == 1

    history = history_qs.first()
    assert history.final_points == stats.total_points
    assert history.correct_answers == stats.correct_answers
    assert history.total_questions == 1
    assert history.final_rank == stats.rank
    assert history.room == room
    assert history.quiz == quiz
