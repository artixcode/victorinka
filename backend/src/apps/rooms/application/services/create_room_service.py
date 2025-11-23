from django.db import transaction

from apps.rooms.domain.value_objects.room_name import RoomName
from apps.rooms.domain.value_objects.invite_code import InviteCode


class CreateRoomService:
    """
    Application Service для создания комнаты.
    """

    @transaction.atomic
    def execute(self, host_id: int, name: str) -> dict:
        """
        Создать новую комнату.
        """
        from apps.rooms.models import Room, RoomParticipant

        room_name_vo = RoomName(name)

        invite_code_vo = self._generate_unique_code()

        room = Room.objects.create(
            name=room_name_vo.value,
            host_id=host_id,
            invite_code=invite_code_vo.value,
            status=Room.Status.DRAFT
        )

        RoomParticipant.objects.create(
            room=room,
            user_id=host_id,
            role=RoomParticipant.Role.HOST
        )


        return {
            "id": room.id,
            "name": room.name,
            "invite_code": room.invite_code,
            "status": room.status,
            "host_id": room.host_id,
            "participants_count": 1
        }

    def _generate_unique_code(self, max_attempts: int = 10) -> InviteCode:
        """
        Сгенерировать уникальный код приглашения.
        """
        from apps.rooms.models import Room

        for _ in range(max_attempts):
            code = InviteCode.generate()

            # Проверка уникальности
            if not Room.objects.filter(invite_code=code.value).exists():
                return code

        raise RuntimeError(
            f"Не удалось сгенерировать уникальный код за {max_attempts} попыток"
        )

