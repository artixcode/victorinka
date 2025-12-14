from django.db import transaction

from apps.rooms.domain.value_objects.room_name import RoomName
from apps.rooms.domain.value_objects.invite_code import InviteCode
from apps.rooms.domain.repositories import RoomRepository
from apps.rooms.infrastructure.orm_room_repository import room_repository


class CreateRoomService:
    """
    Application Service для создания комнаты.
    """

    def __init__(self, repository: RoomRepository = None):
        """
        Инициализация сервиса с репозиторием.
        """
        self.repository = repository or room_repository

    @transaction.atomic
    def execute(self, host_id: int, name: str) -> dict:
        """
        Создать новую комнату.
        """
        from apps.rooms.models import Room, RoomParticipant

        room_name_vo = RoomName(name)

        invite_code_vo = self._generate_unique_code()

        room = self.repository.create(
            name=room_name_vo.value,
            host_id=host_id,
            invite_code=invite_code_vo.value,
            status=Room.Status.DRAFT
        )

        self.repository.add_participant(
            room=room,
            user_id=host_id,
            role=RoomParticipant.Role.HOST
        )

        room.refresh_from_db()

        return {
            "id": room.id,
            "name": room.name,
            "invite_code": room.invite_code,
            "status": room.status,
            "host_id": room.host_id,
            "participants_count": room.participants.count()
        }

    def _generate_unique_code(self, max_attempts: int = 10) -> InviteCode:
        """
        Сгенерировать уникальный код приглашения.
        """
        for _ in range(max_attempts):
            code = InviteCode.generate()

            # Проверка уникальности
            if not self.repository.exists_by_invite_code(code.value):
                return code

        raise RuntimeError(
            f"Не удалось сгенерировать уникальный код за {max_attempts} попыток"
        )

