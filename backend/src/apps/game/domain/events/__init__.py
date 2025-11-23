from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from typing import Optional


def now_utc() -> datetime:
    """Получить текущее время в UTC без зависимости от Django settings"""
    return datetime.now(dt_timezone.utc)


class DomainEvent:
    """
    Базовый класс для всех доменных событий.

    Каждое событие автоматически получает время возникновения.
    """

    def __str__(self):
        return f"{self.__class__.__name__} at {getattr(self, 'occurred_at', 'unknown')}"


@dataclass(frozen=True)
class GameStartedEvent(DomainEvent):
    """
    Событие: игра началась.
    """
    session_id: int
    room_id: int
    quiz_id: int
    host_id: int
    participants_count: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class RoundStartedEvent(DomainEvent):
    """
    Событие: раунд (вопрос) начался.
    """
    session_id: int
    round_id: int
    round_number: int
    question_id: int
    time_limit: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class QuestionAnsweredEvent(DomainEvent):
    """
    Событие: игрок ответил на вопрос.
    """
    session_id: int
    round_id: int
    user_id: int
    answer_id: int
    is_correct: bool
    points_earned: int
    time_taken: float
    is_first_answer: bool
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class RoundCompletedEvent(DomainEvent):
    """
    Событие: раунд завершён.
    """
    session_id: int
    round_id: int
    round_number: int
    correct_answer_id: int
    total_answers: int
    correct_answers_count: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class GameFinishedEvent(DomainEvent):
    """
    Событие: игра завершена.
    """
    session_id: int
    room_id: int
    quiz_id: int
    winner_id: Optional[int]
    total_participants: int
    total_rounds: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class GamePausedEvent(DomainEvent):
    """
    Событие: игра поставлена на паузу.
    """
    session_id: int
    paused_by_user_id: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class GameResumedEvent(DomainEvent):
    """
    Событие: игра продолжена после паузы.
    """
    session_id: int
    resumed_by_user_id: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class PlayerJoinedGameEvent(DomainEvent):
    """
    Событие: игрок присоединился к игре.
    """
    session_id: int
    room_id: int
    user_id: int
    occurred_at: datetime = field(default_factory=now_utc)


@dataclass(frozen=True)
class PlayerLeftGameEvent(DomainEvent):
    """
    Событие: игрок покинул игру.
    """
    session_id: int
    room_id: int
    user_id: int
    reason: str = "left_voluntarily"
    occurred_at: datetime = field(default_factory=now_utc)

