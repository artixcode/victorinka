from typing import Optional, List
from django.db.models import QuerySet

from apps.rooms.domain.repositories import RoomRepository
from apps.rooms.models import Room, RoomParticipant


class ORMRoomRepository(RoomRepository):

    def get_by_id(self, room_id: int) -> Optional[Room]:
        """Получить комнату по ID."""
        try:
            return Room.objects.prefetch_related('participants').get(id=room_id)
        except Room.DoesNotExist:
            return None

    def get_by_invite_code(self, invite_code: str) -> Optional[Room]:
        """Получить комнату по коду приглашения."""
        try:
            return Room.objects.prefetch_related('participants').get(
                invite_code=invite_code.upper()
            )
        except Room.DoesNotExist:
            return None

    def exists_by_invite_code(self, invite_code: str) -> bool:
        """Проверить существование комнаты с таким кодом."""
        return Room.objects.filter(invite_code=invite_code.upper()).exists()

    def create(
        self,
        name: str,
        host_id: int,
        invite_code: str,
        **extra_fields
    ) -> Room:
        """Создать новую комнату."""
        room = Room.objects.create(
            name=name,
            host_id=host_id,
            invite_code=invite_code.upper(),
            **extra_fields
        )
        return room

    def update(self, room: Room, **fields) -> Room:
        """Обновить комнату."""
        for field, value in fields.items():
            setattr(room, field, value)
        room.save(update_fields=list(fields.keys()))
        return room

    def delete(self, room: Room) -> None:
        """Удалить комнату."""
        room.delete()

    def get_user_rooms(self, user_id: int) -> List[Room]:
        """Получить все комнаты пользователя."""
        return list(
            Room.objects
            .filter(participants__user_id=user_id)
            .select_related('host')
            .prefetch_related('participants')
            .order_by('-created_at')
        )

    def get_active_rooms(self, limit: int = 20) -> List[Room]:
        """Получить активные комнаты."""
        return list(
            Room.objects
            .filter(status__in=[Room.Status.OPEN, Room.Status.IN_PROGRESS])
            .select_related('host')
            .prefetch_related('participants')
            .order_by('-created_at')[:limit]
        )

    def add_participant(self, room: Room, user_id: int, role: str = 'player') -> RoomParticipant:
        """Добавить участника в комнату."""
        participant, created = RoomParticipant.objects.get_or_create(
            room=room,
            user_id=user_id,
            defaults={'role': role}
        )
        return participant

    def remove_participant(self, room: Room, user_id: int) -> bool:
        """Удалить участника из комнаты."""
        deleted, _ = RoomParticipant.objects.filter(
            room=room,
            user_id=user_id
        ).delete()
        return deleted > 0

room_repository = ORMRoomRepository()

