from typing import List, Tuple


class RoomCapacityException(Exception):
    """Исключение при превышении лимита участников"""
    pass


class RoomParticipantService:
    """
    Domain Service для управления участниками комнаты.
    """

    MAX_PARTICIPANTS = 10

    def can_join(self, room, user) -> Tuple[bool, str]:
        """
        Проверить может ли пользователь присоединиться к комнате.
        """
        # Проверка статуса комнаты
        if room.status not in ['draft', 'open']:
            return False, "Комната закрыта для присоединения"

        # Проверка лимита участников
        current_count = room.participants.count()
        if current_count >= self.MAX_PARTICIPANTS:
            return False, f"Комната заполнена (максимум {self.MAX_PARTICIPANTS} участников)"

        # Проверка не присоединился ли уже
        if room.participants.filter(user=user).exists():
            return False, "Вы уже в этой комнате"

        return True, ""

    def validate_join_or_raise(self, room, user) -> None:
        """
        Валидация с выбросом исключения.
        """
        can_join, reason = self.can_join(room, user)
        if not can_join:
            raise RoomCapacityException(reason)

    def can_leave(self, room, user) -> Tuple[bool, str]:
        """
        Проверить может ли пользователь покинуть комнату.
        """
        # Хост не может покинуть свою комнату
        if room.host_id == user.id:
            return False, "Хост не может покинуть комнату (удалите комнату вместо этого)"

        # Проверка, что пользователь в комнате
        if not room.participants.filter(user=user).exists():
            return False, "Вы не в этой комнате"

        # Нельзя выйти во время игры
        if room.status == 'in_progress':
            return False, "Нельзя покинуть комнату во время игры"

        return True, ""

    def get_participants_info(self, room) -> dict:
        """
        Получить информацию об участниках комнаты.
        """
        participants_count = room.participants.count()

        return {
            "total": participants_count,
            "max": self.MAX_PARTICIPANTS,
            "available_slots": self.MAX_PARTICIPANTS - participants_count,
            "is_full": participants_count >= self.MAX_PARTICIPANTS,
            "percentage": round((participants_count / self.MAX_PARTICIPANTS) * 100, 1)
        }

