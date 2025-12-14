from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Max, Avg, Count, Min
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, GameHistory
from .serializers import UserLeaderboardSerializer
from apps.questions.models import Quiz


class GlobalLeaderboardView(generics.ListAPIView):
    """
    Глобальная таблица лидеров.
    Сортировка по total_points (очки) и total_wins (победы).
    """
    serializer_class = UserLeaderboardSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Глобальная таблица лидеров. Сортировка по очкам и победам.",
        responses={200: UserLeaderboardSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Сортировка: -total_points (по умолчанию), -total_wins, nickname",
                type=openapi.TYPE_STRING,
                enum=['-total_points', 'total_points', '-total_wins', 'total_wins', 'nickname', '-nickname']
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Количество пользователей (по умолчанию: 100)",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Только активные пользователи с хотя бы одной игрой
        queryset = User.objects.filter(
            is_active=True,
            game_history__isnull=False
        ).distinct()

        # Сортировка
        ordering = self.request.query_params.get('ordering', '-total_points')
        allowed_orderings = ['-total_points', 'total_points', '-total_wins', 'total_wins', 'nickname', '-nickname']

        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering, '-total_points', 'nickname')
        else:
            queryset = queryset.order_by('-total_points', '-total_wins', 'nickname')

        # Лимит результатов
        limit = self.request.query_params.get('limit', 100)
        try:
            limit = int(limit)
            if limit > 0:
                queryset = queryset[:limit]
        except (ValueError, TypeError):
            queryset = queryset[:100]

        return queryset


class QuizLeaderboardView(APIView):
    """
    Таблица лидеров по конкретной викторине.
    Показывает лучшие результаты игроков в этой викторине.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Рейтинг игроков по конкретной викторине (топ результатов)",
        responses={
            200: openapi.Response(
                'Список лучших результатов',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'rank': openapi.Schema(type=openapi.TYPE_INTEGER, description='Место в рейтинге'),
                            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'nickname': openapi.Schema(type=openapi.TYPE_STRING),
                            'total_points': openapi.Schema(type=openapi.TYPE_INTEGER, description='Очки пользователя'),
                            'best_score': openapi.Schema(type=openapi.TYPE_INTEGER, description='Лучший результат в этой викторине'),
                            'games_played': openapi.Schema(type=openapi.TYPE_INTEGER, description='Игр сыграно'),
                            'avg_accuracy': openapi.Schema(type=openapi.TYPE_NUMBER, description='Средняя точность (%)'),
                        }
                    )
                )
            ),
            404: "Викторина не найдена"
        },
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Количество результатов (по умолчанию: 50)",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)

        # Получаем лучшие результаты по этой викторине
        leaderboard_data = GameHistory.objects.filter(
            quiz=quiz
        ).values(
            'user_id',
            'user__nickname',
            'user__total_points'
        ).annotate(
            best_score=Max('final_points'),
            games_played=Count('id'),
            avg_accuracy=Avg('correct_answers') * 100.0 / Avg('total_questions')
        ).order_by('-best_score', '-avg_accuracy')

        # Лимит
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
            if limit > 0:
                leaderboard_data = leaderboard_data[:limit]
        except (ValueError, TypeError):
            leaderboard_data = leaderboard_data[:50]

        # Добавляем ранги
        results = []
        for rank, entry in enumerate(leaderboard_data, start=1):
            results.append({
                'rank': rank,
                'user_id': entry['user_id'],
                'nickname': entry['user__nickname'],
                'total_points': entry['user__total_points'],
                'best_score': entry['best_score'],
                'games_played': entry['games_played'],
                'avg_accuracy': round(entry['avg_accuracy'] or 0, 1),
            })

        return Response({
            'quiz_id': quiz_id,
            'quiz_title': quiz.title,
            'leaderboard': results
        })


class RoomLeaderboardView(APIView):
    """
    Таблица лидеров по конкретной комнате (результаты игр в этой комнате).
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Рейтинг игроков по комнате (все игры в этой комнате)",
        responses={
            200: openapi.Response(
                'Список результатов',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'rank': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'nickname': openapi.Schema(type=openapi.TYPE_STRING),
                            'best_score': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'games_played': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'avg_rank': openapi.Schema(type=openapi.TYPE_NUMBER, description='Среднее место'),
                        }
                    )
                )
            ),
            404: "Комната не найдена"
        }
    )
    def get(self, request, room_id):
        from apps.rooms.models import Room

        room = get_object_or_404(Room, id=room_id)

        # Получаем результаты по комнате
        leaderboard_data = GameHistory.objects.filter(
            room=room
        ).values(
            'user_id',
            'user__nickname'
        ).annotate(
            best_score=Max('final_points'),
            games_played=Count('id'),
            avg_rank=Avg('final_rank'),
            best_rank=Min('final_rank')
        ).order_by('-best_score', 'avg_rank')[:50]

        # Добавляем ранги
        results = []
        for rank, entry in enumerate(leaderboard_data, start=1):
            results.append({
                'rank': rank,
                'user_id': entry['user_id'],
                'nickname': entry['user__nickname'],
                'best_score': entry['best_score'],
                'games_played': entry['games_played'],
                'avg_rank': round(entry['avg_rank'] or 0, 1),
                'best_rank': entry['best_rank'] or 0,
            })

        return Response({
            'room_id': room_id,
            'room_name': room.name,
            'leaderboard': results
        })


class UserStatsDetailView(APIView):
    """
    Детальная статистика конкретного пользователя для лидерборда.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Детальная статистика пользователя",
        responses={
            200: openapi.Response(
                'Статистика пользователя',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'nickname': openapi.Schema(type=openapi.TYPE_STRING),
                        'total_points': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_wins': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_games': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'global_rank': openapi.Schema(type=openapi.TYPE_INTEGER, description='Место в глобальном рейтинге'),
                        'avg_accuracy': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'best_game_points': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            404: "Пользователь не найден"
        }
    )
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # Общая статистика
        total_games = user.game_history.count()

        # Средняя точность
        from django.db.models import Avg
        avg_accuracy_data = user.game_history.aggregate(
            avg=Avg('correct_answers') * 100.0 / Avg('total_questions')
        )
        avg_accuracy = round(avg_accuracy_data['avg'] or 0, 1)

        # Лучшая игра
        best_game = user.game_history.order_by('-final_points').first()
        best_game_points = best_game.final_points if best_game else 0

        # Глобальный ранг
        global_rank = User.objects.filter(
            is_active=True,
            total_points__gt=user.total_points
        ).count() + 1

        return Response({
            'user_id': user.id,
            'nickname': user.nickname,
            'email': user.email if request.user == user or request.user.is_staff else None,
            'total_points': user.total_points,
            'total_wins': user.total_wins,
            'total_games': total_games,
            'global_rank': global_rank,
            'avg_accuracy': avg_accuracy,
            'best_game_points': best_game_points,
        })

