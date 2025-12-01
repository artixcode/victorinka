import pytest
from model_bakery import baker
from apps.rooms.models import RoomParticipant


@pytest.mark.django_db
def test_my_rooms_list(auth_client, user):
    room1 = baker.make("rooms.Room", host=user)
    room2 = baker.make("rooms.Room", host=user)

    RoomParticipant.objects.create(room=room1, user=user, role="host")
    RoomParticipant.objects.create(room=room2, user=user, role="host")

    res = auth_client.get("/api/rooms/mine/")

    assert res.status_code == 200
    assert res.data["count"] == 2
    assert len(res.data["results"]) == 2


@pytest.mark.django_db
def test_create_room(auth_client, user):
    payload = {"name": "Test room"}

    res = auth_client.post("/api/rooms/", payload, format="json")

    assert res.status_code == 201
    assert res.data["name"] == "Test room"
    assert "id" in res.data
    assert "invite_code" in res.data


@pytest.mark.django_db
def test_room_detail(auth_client, user):
    room = baker.make("rooms.Room", host=user)
    RoomParticipant.objects.create(room=room, user=user, role="host")

    res = auth_client.get(f"/api/rooms/{room.id}/")

    assert res.status_code == 200
    assert res.data["id"] == room.id
    assert res.data["name"] == room.name

@pytest.mark.django_db
def test_leave_room(auth_client, user):
    host = baker.make("users.User")
    room = baker.make("rooms.Room", host=host, status="open")

    RoomParticipant.objects.create(room=room, user=user)

    res = auth_client.post(f"/api/rooms/{room.id}/leave/")

    assert res.status_code == 200
    assert not RoomParticipant.objects.filter(room=room, user=user).exists()


@pytest.mark.django_db
def test_join_room_with_wrong_code_returns_400(auth_client, user):
    """Неверный код приглашения → 400 и участник не создаётся"""
    host = baker.make("users.User")
    room = baker.make("rooms.Room", host=host, status="open", invite_code="ABC123")

    res = auth_client.post(
        f"/api/rooms/{room.id}/join/",
        {"invite_code": "WRONG"},
        format="json",
    )

    assert res.status_code == 400
    assert "Неверный код" in res.data["detail"]
    assert not RoomParticipant.objects.filter(room=room, user=user).exists()


@pytest.mark.django_db
def test_join_closed_room_returns_400(auth_client, user):
    """Комната с корректным кодом, но статус finished → 400"""
    host = baker.make("users.User")
    room = baker.make("rooms.Room", host=host, status="finished", invite_code="ABC123")

    res = auth_client.post(
        f"/api/rooms/{room.id}/join/",
        {"invite_code": "ABC123"},
        format="json",
    )

    assert res.status_code == 400
    assert "комната закрыта" in res.data["detail"]
    assert not RoomParticipant.objects.filter(room=room, user=user).exists()


@pytest.mark.django_db
def test_join_same_room_twice_returns_joined_false(auth_client, user):
    """При повторном join вернётся joined=False и не создастся второй participant"""
    host = baker.make("users.User")
    room = baker.make("rooms.Room", host=host, status="open", invite_code="ABC123")

    # Первый успешный join
    res1 = auth_client.post(
        f"/api/rooms/{room.id}/join/",
        {"invite_code": "ABC123"},
        format="json",
    )
    assert res1.status_code == 200
    assert res1.data["joined"] is True
    assert RoomParticipant.objects.filter(room=room, user=user).count() == 1

    # Повторный join
    res2 = auth_client.post(
        f"/api/rooms/{room.id}/join/",
        {"invite_code": "ABC123"},
        format="json",
    )
    assert res2.status_code == 200
    assert res2.data["joined"] is False
    assert RoomParticipant.objects.filter(room=room, user=user).count() == 1


@pytest.mark.django_db
def test_host_cannot_leave_room_via_api(auth_client, user):
    """Хост не может выйти из комнаты через /leave/"""
    # user из фикстуры — это как раз авторизованный пользователь для auth_client
    room = baker.make("rooms.Room", host=user, status="open")
    RoomParticipant.objects.create(room=room, user=user, role="host")

    res = auth_client.post(f"/api/rooms/{room.id}/leave/")

    assert res.status_code == 400
    assert "Хост не может поки" in res.data["detail"]  # начало сообщения
    assert RoomParticipant.objects.filter(room=room, user=user).exists()