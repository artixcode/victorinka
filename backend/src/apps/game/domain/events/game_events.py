from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .room_events import RoomEvent


@dataclass
class GameStarted(RoomEvent):
    """Событие: игра началась."""
    session_id: int = 0
    quiz_id: int = 0
    quiz_title: str = ""
    total_questions: int = 0
    started_by: int = 0  # user_id хоста


@dataclass
class QuestionRevealed(RoomEvent):
    """Событие: показан новый вопрос игрокам."""
    session_id: int = 0
    round_number: int = 0
    question_id: int = 0
    question_text: str = ""
    options: List[Dict] = field(default_factory=list)
    time_limit: int = 30
    points: int = 0
    difficulty: str = "medium"


@dataclass
class PlayerAnswerSubmitted(RoomEvent):
    """Событие: игрок отправил ответ."""
    session_id: int = 0
    round_number: int = 0
    user_id: int = 0
    username: str = ""
    answer_option_id: int = 0
    time_taken: float = 0.0
    is_first: bool = False


@dataclass
class AnswerChecked(RoomEvent):
    """Событие: ответ проверен системой."""
    session_id: int = 0
    round_number: int = 0
    user_id: int = 0
    username: str = ""
    is_correct: bool = False
    points_earned: int = 0
    time_taken: float = 0.0
    current_score: int = 0


@dataclass
class RoundCompleted(RoomEvent):
    """Событие: раунд завершен, показаны результаты."""
    session_id: int = 0
    round_number: int = 0
    question_id: int = 0
    correct_option_id: int = 0
    explanation: str = ""
    results: List[Dict] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)


@dataclass
class GameFinished(RoomEvent):
    """Событие: игра завершена, показаны итоги."""
    session_id: int = 0
    quiz_title: str = ""
    total_rounds: int = 0
    final_results: List[Dict] = field(default_factory=list)
    winner_id: Optional[int] = None
    winner_username: Optional[str] = None


@dataclass
class GamePaused(RoomEvent):
    """Событие: игра поставлена на паузу."""
    session_id: int = 0
    paused_by: int = 0
    current_round: int = 0


@dataclass
class GameResumed(RoomEvent):
    """Событие: игра продолжена после паузы."""
    session_id: int = 0
    resumed_by: int = 0
    current_round: int = 0

