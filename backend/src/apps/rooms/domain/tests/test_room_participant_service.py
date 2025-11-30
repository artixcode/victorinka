import pytest
from model_bakery import baker

from apps.rooms.domain.services.room_participant_service import (
    RoomParticipantService,
    RoomCapacityException,
)
from apps.rooms.models import RoomParticipant, Room


@pytest.mark.django_db
class TestRoomParticipantService:
    def setup_method(self):
        self.service = RoomParticipantService()

    def test_can_join_open_room_when_not_full_and_not_in_room(self, user):
        """Открытая комната, не заполнена, юзер ещё не участник → можно зайти"""
        room = baker.make("rooms.Room", status=Room.Status.OPEN)

        can_join, reason = self.service.can_join(room, user)

        assert can_join is True
        assert reason == ""

    def test_cannot_join_closed_room(self, user):
        """Статус не draft/open → отказ"""
        room = baker.make("rooms.Room", status=Room.Status.FINISHED)

        can_join, reason = self.service.can_join(room, user)

        assert can_join is False
        assert "Комната закрыта" in reason

    def test_cannot_join_when_room_full(self, user):
        """Если участников уже MAX_PARTICIPANTS → отказ"""
        room = baker.make("rooms.Room", status=Room.Status.OPEN)

        # создаём MAX_PARTICIPANTS разных пользователей с уникальными nickname
        for i in range(RoomParticipantService.MAX_PARTICIPANTS):
            participant_user = baker.make(
                "users.User",
                nickname=f"player_{i}",
            )
            RoomParticipant.objects.create(room=room, user=participant_user)

        can_join, reason = self.service.can_join(room, user)

        assert can_join is False
        assert str(RoomParticipantService.MAX_PARTICIPANTS) in reason

    def test_cannot_join_when_already_participant(self, user):
        """Если пользователь уже в комнате → отказ"""
        room = baker.make("rooms.Room", status=Room.Status.OPEN)
        RoomParticipant.objects.create(room=room, user=user)

        can_join, reason = self.service.can_join(room, user)

        assert can_join is False
        assert "уже в этой комнате" in reason

    def test_validate_join_or_raise_raises_exception(self, user):
        """validate_join_or_raise поднимает RoomCapacityException при отказе"""
        room = baker.make("rooms.Room", status=Room.Status.FINISHED)

        with pytest.raises(RoomCapacityException):
            self.service.validate_join_or_raise(room, user)

    def test_host_cannot_leave_room(self, user):
        """Хост не может покинуть комнату"""
        room = baker.make("rooms.Room", host=user, status=Room.Status.OPEN)

        can_leave, reason = self.service.can_leave(room, user)

        assert can_leave is False
        assert "Хост не может покинуть комнату" in reason

    def test_cannot_leave_if_not_participant(self, user):
        """Пользователь не в комнате → отказ при выходе"""
        host = baker.make("users.User")
        room = baker.make("rooms.Room", host=host, status=Room.Status.OPEN)

        can_leave, reason = self.service.can_leave(room, user)

        assert can_leave is False
        assert "Вы не в этой комнате" in reason

    def test_cannot_leave_while_in_progress(self, user):
        """Нельзя выйти во время игры (status=in_progress)"""
        host = baker.make("users.User")
        room = baker.make("rooms.Room", host=host, status=Room.Status.IN_PROGRESS)
        RoomParticipant.objects.create(room=room, user=user)

        can_leave, reason = self.service.can_leave(room, user)

        assert can_leave is False
        assert "во время игры" in reason

    def test_can_leave_when_regular_participant_in_open_room(self, user):
        """Обычный участник может выйти из открытой комнаты"""
        host = baker.make("users.User")
        room = baker.make("rooms.Room", host=host, status=Room.Status.OPEN)
        RoomParticipant.objects.create(room=room, user=user)

        can_leave, reason = self.service.can_leave(room, user)

        assert can_leave is True
        assert reason == ""

    def test_get_participants_info(self, user):
        """get_participants_info возвращает корректную статистику"""
        room = baker.make("rooms.Room", status=Room.Status.OPEN)

        # уже есть user из фикстуры
        RoomParticipant.objects.create(room=room, user=user)

        # создаём ещё двух с уникальными nickname
        user2 = baker.make("users.User", nickname="user2")
        user3 = baker.make("users.User", nickname="user3")

        RoomParticipant.objects.create(room=room, user=user2)
        RoomParticipant.objects.create(room=room, user=user3)

        info = self.service.get_participants_info(room)

        assert info["total"] == 3
        assert info["max"] == RoomParticipantService.MAX_PARTICIPANTS
        assert info["available_slots"] == RoomParticipantService.MAX_PARTICIPANTS - 3
        assert info["is_full"] is False
        assert info["percentage"] == 3 / RoomParticipantService.MAX_PARTICIPANTS * 100

