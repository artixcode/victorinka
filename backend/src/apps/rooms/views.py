from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Room, RoomParticipant
from .serializers import RoomSerializer, RoomCreateSerializer, RoomPatchSerializer
from .permissions import IsRoomHost
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class MyRoomsListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        room_ids = RoomParticipant.objects.filter(user=user).values_list("room_id", flat=True)
        return Room.objects.filter(participants__user=user).order_by("-created_at")


class RoomCreateView(generics.CreateAPIView):
    serializer_class = RoomCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=RoomCreateSerializer, responses={201: RoomSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        room = serializer.save(host=self.request.user)
        RoomParticipant.objects.get_or_create(
            room=room, user=self.request.user, defaults={"role": RoomParticipant.Role.HOST}
        )
        self.room = room

    def create(self, request, *args, **kwargs):
        super_response = super().create(request, *args, **kwargs)
        data = RoomSerializer(self.room, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [permissions.IsAuthenticated(), IsRoomHost()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return RoomPatchSerializer
        return RoomSerializer


class RoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["invite_code"],
            properties={
                "invite_code": openapi.Schema(type=openapi.TYPE_STRING, example="ABCD12"),
            },
        ),
        responses={200: openapi.Response("OK")}
    )
    def post(self, request, pk: int):
        room = get_object_or_404(Room, pk=pk)
        code = (request.data.get("invite_code") or "").strip().upper()
        if room.invite_code != code or room.status not in (Room.Status.DRAFT, Room.Status.OPEN):
            return Response({"detail": "Неверный код или комната закрыта"}, status=400)

        _, created = RoomParticipant.objects.get_or_create(room=room, user=request.user)
        return Response({"detail": "Вы в комнате", "joined": created}, status=200)


class RoomLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={},
        ),
        responses={200: openapi.Response("OK")}
    )
    def post(self, request, pk: int):
        room = get_object_or_404(Room, pk=pk)
        if room.host_id == request.user.id:
            return Response({"detail": "Хост не может покинуть комнату. Передайте хостинг или удалите комнату."}, status=400)
        RoomParticipant.objects.filter(room=room, user=request.user).delete()
        return Response({"detail": "Вы вышли из комнаты"}, status=200)
