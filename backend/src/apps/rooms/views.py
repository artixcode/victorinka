from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Room, RoomParticipant
from .serializers import RoomSerializer, RoomCreateSerializer, RoomPatchSerializer
from .permissions import IsRoomHost
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .application.services.create_room_service import CreateRoomService
from .application.services.join_room_service import JoinRoomService
from apps.rooms.domain.services.room_participant_service import RoomCapacityException


class MyRoomsListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Room.objects.filter(
            participants__user=user
        ).prefetch_related('participants').order_by("-created_at")


class RoomCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=RoomCreateSerializer, 
        responses={201: RoomSerializer}
    )
    def post(self, request):
        service = CreateRoomService()
        
        try:
            result = service.execute(
                host_id=request.user.id,
                name=request.data.get('name', 'Новая комната')
            )
            
            # Возвращаем результат
            return Response(result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Ошибка создания комнаты: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Room.objects.prefetch_related('participants').all()

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
        service = JoinRoomService()
        
        try:
            invite_code = request.data.get("invite_code", "").strip()
            
            result = service.execute(
                user_id=request.user.id,
                invite_code=invite_code
            )
            
            return Response({
                "detail": "Вы присоединились к комнате",
                "joined": True,
                **result
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RoomCapacityException as e:
            error_message = str(e)
            if "уже в этой комнате" in error_message.lower():
                room = get_object_or_404(Room, pk=pk)
                return Response({
                    "detail": error_message,
                    "joined": False,
                    "room_id": room.id,
                    "room_name": room.name
                }, status=status.HTTP_200_OK)

            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Ошибка присоединения: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


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


class RoomFindView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'invite_code',
                openapi.IN_QUERY,
                description="Код приглашения комнаты",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: RoomSerializer,
            404: "Комната не найдена"
        }
    )
    def get(self, request):
        invite_code = request.query_params.get('invite_code', '').strip().upper()

        if not invite_code:
            return Response(
                {"detail": "Код приглашения не указан"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            room = Room.objects.prefetch_related('participants').get(invite_code=invite_code)
            serializer = RoomSerializer(room)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Комната с таким кодом не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )