from abc import ABC, abstractmethod
from typing import Optional, List


class RoomRepository(ABC):

    @abstractmethod
    def get_by_id(self, room_id: int):
        """Получить комнату по ID."""
        pass

    @abstractmethod
    def get_by_invite_code(self, invite_code: str):
        """Получить комнату по коду приглашения."""
        pass

    @abstractmethod
    def exists_by_invite_code(self, invite_code: str) -> bool:
        """Проверить существование комнаты с таким кодом."""
        pass

    @abstractmethod
    def create(
        self,
        name: str,
        host_id: int,
        invite_code: str,
        **extra_fields
    ):
        """Создать новую комнату."""
        pass

    @abstractmethod
    def update(self, room, **fields):
        """Обновить комнату."""
        pass

    @abstractmethod
    def delete(self, room) -> None:
        """Удалить комнату."""
        pass

    @abstractmethod
    def get_user_rooms(self, user_id: int) -> List:
        """Получить все комнаты пользователя."""
        pass

    @abstractmethod
    def get_active_rooms(self, limit: int = 20) -> List:
        """Получить активные комнаты."""
        pass

