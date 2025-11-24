from rest_framework import views, permissions, status, generics, filters
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer, LoginSerializer, MeSerializer, ProfileUpdateSerializer,
    QuizBookmarkSerializer, QuizBookmarkCreateSerializer,
    GameHistorySerializer, UserStatsSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, PasswordResetTokenSerializer
)
from .models import QuizBookmark, GameHistory, PasswordResetToken
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.shortcuts import get_object_or_404

User = get_user_model()


class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: openapi.Response("Аккаунт создан", RegisterSerializer)},
        examples={"application/json": {"email": "player@mail.com", "password": "Qwerty123", "nickname": "PlayerOne"}}
    )
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("OK", LoginSerializer)}
    )
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class MeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)

    @swagger_auto_schema(
        request_body=ProfileUpdateSerializer,
        responses={200: MeSerializer},
        examples={"application/json": {"nickname": "NewNick"}}
    )
    def patch(self, request):
        s = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(MeSerializer(request.user).data)


class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            },
        ),
        responses={
            200: openapi.Response("OK"),
            400: "Некорректный запрос",
            401: "Неавторизован",
        },
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "Refresh токен обязателен"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response({"detail": "Некорректный refresh токен"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Вы вышли из системы"}, status=status.HTTP_200_OK)


class LogoutAllView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={200: "Все сессии отозваны"})
    def post(self, request):
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            BlacklistedToken.objects.get_or_create(token=t)
        return Response({"detail": "Вы вышли из всех устройств"}, status=status.HTTP_200_OK)


class MyBookmarksListView(generics.ListAPIView):
    """Список закладок пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizBookmarkSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['added_at', 'quiz__title', 'quiz__views_count']
    ordering = ['-added_at']

    def get_queryset(self):
        return QuizBookmark.objects.filter(user=self.request.user).select_related('quiz', 'quiz__author')


class BookmarkCreateView(views.APIView):
    """Добавить викторину в закладки"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=QuizBookmarkCreateSerializer,
        responses={
            201: QuizBookmarkSerializer,
            400: "Викторина уже в закладках или некорректные данные"
        }
    )
    def post(self, request):
        serializer = QuizBookmarkCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            quiz_id = serializer.validated_data['quiz'].id
            if QuizBookmark.objects.filter(user=request.user, quiz_id=quiz_id).exists():
                return Response(
                    {"error": "Эта викторина уже в ваших закладках"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            bookmark = serializer.save()
            return Response(
                QuizBookmarkSerializer(bookmark).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookmarkDetailView(views.APIView):
    """Получить, обновить или удалить закладку"""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(QuizBookmark, pk=pk, user=self.request.user)

    @swagger_auto_schema(responses={200: QuizBookmarkSerializer})
    def get(self, request, pk):
        bookmark = self.get_object(pk)
        return Response(QuizBookmarkSerializer(bookmark).data)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'notes': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={200: QuizBookmarkSerializer}
    )
    def patch(self, request, pk):
        bookmark = self.get_object(pk)
        notes = request.data.get('notes', '')
        bookmark.notes = notes
        bookmark.save()
        return Response(QuizBookmarkSerializer(bookmark).data)

    @swagger_auto_schema(responses={204: "Закладка удалена"})
    def delete(self, request, pk):
        bookmark = self.get_object(pk)
        bookmark.delete()
        return Response({"detail": "Закладка удалена"}, status=status.HTTP_204_NO_CONTENT)


class MyGameHistoryView(generics.ListAPIView):
    """История игр пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GameHistorySerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['played_at', 'final_points', 'accuracy']
    ordering = ['-played_at']

    def get_queryset(self):
        return GameHistory.objects.filter(user=self.request.user).select_related(
            'quiz', 'room', 'session'
        )


class MyActiveRoomsView(views.APIView):
    """Активные комнаты пользователя"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={200: openapi.Response(
            'Список активных комнат',
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'room_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'room_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'is_host': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'joined_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                    }
                )
            )
        )}
    )
    def get(self, request):
        from apps.rooms.models import Room, RoomParticipant

        participations = RoomParticipant.objects.filter(
            user=request.user,
            room__status__in=[Room.Status.OPEN, Room.Status.IN_PROGRESS]
        ).select_related('room').order_by('-joined_at')

        active_rooms = []
        for participation in participations:
            room = participation.room
            active_rooms.append({
                'room_id': room.id,
                'room_name': room.name,
                'invite_code': room.invite_code,
                'status': room.status,
                'is_host': participation.role == RoomParticipant.Role.HOST,
                'joined_at': participation.joined_at,
                'participants_count': room.participants.count(),
            })

        return Response(active_rooms)


class MyStatsView(views.APIView):
    """Статистика пользователя"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={200: UserStatsSerializer})
    def get(self, request):
        serializer = UserStatsSerializer(request.user)
        return Response(serializer.data)


class PasswordResetRequestView(views.APIView):
    """Запрос на восстановление пароля."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                'Токен создан',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Email не найден"
        },
        examples={
            "application/json": {"email": "user@example.com"}
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Создаем токен восстановления
        reset_token = PasswordResetToken.objects.create(user=user)

        return Response({
            'detail': 'Запрос на восстановление пароля создан',
            'message': f'Токен восстановления создан для {email}. '
                      'Администратор может найти токен в базе данных или админ-панели '
                      'и передать его вам любым удобным способом.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(views.APIView):
    """Подтверждение восстановления пароля с токеном."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response('Пароль успешно изменен'),
            400: "Некорректные данные или токен"
        },
        examples={
            "application/json": {
                "token": "abc123xyz789def456ghi012jkl345mn",
                "new_password": "NewSecurePassword123"
            }
        }
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_value = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        # Получаем токен и пользователя
        reset_token = PasswordResetToken.objects.get(token=token_value)
        user = reset_token.user

        # Меняем пароль
        user.set_password(new_password)
        user.save()

        # Помечаем токен как использованный
        ip_address = request.META.get('REMOTE_ADDR')
        reset_token.mark_as_used(ip_address=ip_address)

        return Response({
            'detail': 'Пароль успешно изменен',
            'message': 'Теперь вы можете войти с новым паролем'
        }, status=status.HTTP_200_OK)


class PasswordResetTokenListView(generics.ListAPIView):
    """Список токенов восстановления (только для администраторов)."""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = PasswordResetTokenSerializer
    queryset = PasswordResetToken.objects.all().select_related('user').order_by('-created_at')

    @swagger_auto_schema(
        responses={200: PasswordResetTokenSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


