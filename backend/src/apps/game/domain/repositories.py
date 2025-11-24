from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class IGameSessionRepository(ABC):
    """
    Интерфейс репозитория для GameSession.
    """

    @abstractmethod
    def get_by_id(self, session_id: int):
        """
        Получить сессию по ID.
        """
        pass

    @abstractmethod
    def save(self, session) -> None:
        """
        Сохранить сессию.
        """
        pass

    @abstractmethod
    def get_active_sessions_for_room(self, room_id: int) -> List:
        """
        Получить активные сессии для комнаты.
        """
        pass

    @abstractmethod
    def find_by_room_and_status(self, room_id: int, statuses: List[str]) -> Optional:
        """
        Найти сессию по комнате и статусам.
        """
        pass


class IGameRoundRepository(ABC):
    """Интерфейс репозитория для GameRound."""

    @abstractmethod
    def get_by_id(self, round_id: int):
        """Получить раунд по ID."""
        pass

    @abstractmethod
    def save(self, round) -> None:
        """Сохранить раунд."""
        pass

    @abstractmethod
    def get_rounds_for_session(self, session_id: int) -> List:
        """
        Получить все раунды для сессии.
        """
        pass

    @abstractmethod
    def get_current_round(self, session_id: int, round_number: int) -> Optional:
        """
        Получить текущий раунд.
        """
        pass

    @abstractmethod
    def bulk_create(self, rounds: List) -> None:
        """
        Массово создать раунды.
        """
        pass


class IPlayerGameStatsRepository(ABC):

    @abstractmethod
    def get_by_session_and_user(self, session_id: int, user_id: int):
        """
        Получить статистику игрока в сессии.
        """
        pass

    @abstractmethod
    def save(self, stats) -> None:
        """Сохранить статистику."""
        pass

    @abstractmethod
    def get_all_for_session(self, session_id: int) -> List:
        """
        Получить статистику всех игроков в сессии.
        """
        pass

    @abstractmethod
    def get_leaderboard(self, session_id: int) -> List:
        """
        Получить таблицу лидеров (отсортированную по очкам).
        """
        pass


class IRoomStateRepository(ABC):

    @abstractmethod
    def add_player(self, room_id: int, user_id: int, username: str, channel_name: str) -> None:
        """Добавить игрока в комнату."""
        pass

    @abstractmethod
    def remove_player(self, room_id: int, user_id: int) -> None:
        """Удалить игрока из комнаты."""
        pass

    @abstractmethod
    def get_players(self, room_id: int) -> List[dict]:
        """Получить список всех игроков в комнате."""
        pass

    @abstractmethod
    def get_player_count(self, room_id: int) -> int:
        """Получить количество игроков в комнате."""
        pass

    @abstractmethod
    def is_player_in_room(self, room_id: int, user_id: int) -> bool:
        """Проверить, находится ли игрок в комнате."""
        pass

    @abstractmethod
    def add_message(self, room_id: int, user_id: int, username: str, message: str) -> None:
        """Добавить сообщение в чат комнаты."""
        pass

    @abstractmethod
    def get_recent_messages(self, room_id: int, limit: int = 50) -> List[dict]:
        """Получить последние N сообщений чата."""
        pass

    @abstractmethod
    def clear_room(self, room_id: int) -> None:
        """Очистить всё состояние комнаты (при завершении игры)."""
        pass

    @abstractmethod
    def bulk_create(self, stats_list: List) -> None:
        """
        Массово создать статистику.
        """
        pass


class IPlayerAnswerRepository(ABC):
    @abstractmethod
    def get_by_id(self, answer_id: int):
        """Получить ответ по ID."""
        pass

    @abstractmethod
    def save(self, answer) -> None:
        """Сохранить ответ."""
        pass

    @abstractmethod
    def get_answers_for_round(self, round_id: int) -> List:
        """
        Получить все ответы для раунда.
        """
        pass

    @abstractmethod
    def has_user_answered(self, round_id: int, user_id: int) -> bool:
        """
        Проверить, ответил ли пользователь на раунд.
        """
        pass

    @abstractmethod
    def get_user_answer(self, round_id: int, user_id: int) -> Optional:
        """
        Получить ответ пользователя на раунд.
        """
        pass


class RepositoryException(Exception):
    """Базовое исключение для репозиториев."""
    pass


class EntityNotFoundException(RepositoryException):
    """Исключение когда сущность не найдена."""

    def __init__(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} с ID {entity_id} не найден")


class DuplicateEntityException(RepositoryException):
    """Исключение когда сущность уже существует."""
    pass

