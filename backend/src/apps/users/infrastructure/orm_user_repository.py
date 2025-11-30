from typing import Optional, List
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.users.domain.repositories import UserRepository


User = get_user_model()


class ORMUserRepository(UserRepository):

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def exists_by_email(self, email: str) -> bool:
        """Проверить существование пользователя по email."""
        return User.objects.filter(email=email).exists()

    def create(
        self,
        email: str,
        password: str,
        nickname: str,
        **extra_fields
    ) -> User:
        """Создать нового пользователя."""
        user = User.objects.create_user(
            email=email,
            password=password,
            nickname=nickname,
            **extra_fields
        )
        return user

    def update(self, user: User, **fields) -> User:
        """Обновить пользователя."""
        for field, value in fields.items():
            setattr(user, field, value)
        user.save(update_fields=list(fields.keys()))
        return user

    def delete(self, user: User) -> None:
        """Удалить пользователя."""
        user.delete()

    def get_top_players(self, limit: int = 10) -> List[User]:
        """Получить топ игроков по очкам."""
        return list(
            User.objects
            .filter(is_active=True)
            .order_by('-total_points', '-total_wins')[:limit]
        )

    def get_all_active(self) -> QuerySet:
        """Получить всех активных пользователей."""
        return User.objects.filter(is_active=True)


# Singleton instance
user_repository = ORMUserRepository()

