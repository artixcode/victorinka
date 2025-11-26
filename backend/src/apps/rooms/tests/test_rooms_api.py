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
