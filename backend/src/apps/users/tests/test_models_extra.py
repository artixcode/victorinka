import pytest
from datetime import timedelta

from django.utils import timezone

from apps.users.models import GameHistory, PasswordResetToken
from apps.rooms.models import Room
from apps.game.models import GameSession
from apps.questions.models import Quiz


# ---------- GameHistory.accuracy ----------

@pytest.mark.django_db
def test_game_history_accuracy_zero_when_no_questions(user):
    """
    Если total_questions = 0, accuracy должен быть 0,
    и при этом не должно быть деления на ноль.
    """
    # создаём минимальный набор связанных объектов руками, без bakery
    room = Room.objects.create(
        name="Test room",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="Test quiz",
    )
    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
    )

    history = GameHistory.objects.create(
        user=user,
        session=session,
        room=room,
        quiz=quiz,
        total_questions=0,
        correct_answers=0,
        final_points=0,
    )

    assert history.accuracy == 0


@pytest.mark.django_db
def test_game_history_accuracy_calculated_correctly(user):
    """accuracy = round(correct / total * 100, 1)."""
    room = Room.objects.create(
        name="Test room",
        host=user,
        status=Room.Status.FINISHED,
    )
    quiz = Quiz.objects.create(
        author=user,
        title="Test quiz",
    )
    session = GameSession.objects.create(
        room=room,
        quiz=quiz,
    )

    history = GameHistory.objects.create(
        user=user,
        session=session,
        room=room,
        quiz=quiz,
        total_questions=20,
        correct_answers=13,
        final_points=0,
    )

    # 13 / 20 * 100 = 65.0
    assert history.accuracy == 65.0


# ---------- PasswordResetToken ----------

@pytest.mark.django_db
def test_password_reset_token_is_expired_and_is_valid_flags(user):
    """Проверяем is_expired и is_valid в зависимости от expires_at / is_used."""
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1),
        is_used=False,
    )

    # Истёкший токен
    token.expires_at = timezone.now() - timedelta(hours=1)
    token.is_used = False
    token.save(update_fields=["expires_at", "is_used"])

    assert token.is_expired() is True
    assert token.is_valid() is False

    # Не истёк, но использован
    token.expires_at = timezone.now() + timedelta(hours=1)
    token.is_used = True
    token.save(update_fields=["expires_at", "is_used"])

    assert token.is_expired() is False
    assert token.is_valid() is False


@pytest.mark.django_db
def test_password_reset_token_mark_as_used(user):
    """mark_as_used помечает токен использованным, задаёт used_at и ip_address."""
    token = PasswordResetToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=1),
        is_used=False,
    )

    token.mark_as_used(ip_address="127.0.0.1")
    token.refresh_from_db()

    assert token.is_used is True
    assert token.used_at is not None
    assert token.ip_address == "127.0.0.1"
    assert token.is_valid() is False
