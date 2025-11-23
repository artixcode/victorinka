from django.db import transaction

from apps.rooms.domain.value_objects.invite_code import InviteCode
from apps.rooms.domain.services.room_participant_service import (
    RoomParticipantService,
    RoomCapacityException
)


class JoinRoomService:
    """
    Application Service для присоединения к комнате.
    """
    
    def __init__(self, participant_service: RoomParticipantService = None):
        """
        Инициализация сервиса.
        """
        self.participant_service = participant_service or RoomParticipantService()
    
    @transaction.atomic
    def execute(self, user_id: int, invite_code: str) -> dict:
        """
        Присоединиться к комнате по коду приглашения.
        """
        from apps.rooms.models import Room, RoomParticipant
        from django.contrib.auth import get_user_model
        
        User = get_user_model()

        invite_code_vo = InviteCode.from_string(invite_code)

        try:
            room = Room.objects.prefetch_related('participants').get(
                invite_code=invite_code_vo.value
            )
        except Room.DoesNotExist:
            raise ValueError(f"Комната с кодом {invite_code_vo.value} не найдена")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"Пользователь с ID {user_id} не найден")

        self.participant_service.validate_join_or_raise(room, user)

        participant = RoomParticipant.objects.create(
            room=room,
            user=user,
            role=RoomParticipant.Role.PLAYER
        )

        
        participants_info = self.participant_service.get_participants_info(room)
        
        return {
            "room_id": room.id,
            "room_name": room.name,
            "participant_id": participant.id,
            "role": participant.role,
            "participants_total": participants_info['total'],
            "available_slots": participants_info['available_slots'],
            "joined_at": participant.joined_at
        }

