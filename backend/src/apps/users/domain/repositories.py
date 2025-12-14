from abc import ABC, abstractmethod
from typing import Optional, List
from django.contrib.auth import get_user_model


User = get_user_model()


class UserRepository(ABC):

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Проверить существование пользователя по email."""
        pass

    @abstractmethod
    def create(
        self,
        email: str,
        password: str,
        nickname: str,
        **extra_fields
    ) -> User:
        """Создать нового пользователя."""
        pass

    @abstractmethod
    def update(self, user: User, **fields) -> User:
        """Обновить пользователя."""
        pass

    @abstractmethod
    def delete(self, user: User) -> None:
        """Удалить пользователя."""
        pass

    @abstractmethod
    def get_top_players(self, limit: int = 10) -> List[User]:
        """Получить топ игроков по очкам."""
        pass

