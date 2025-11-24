from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone

from .models import GameSession, GameRound, PlayerAnswer, PlayerGameStats
from .serializers import (
    GameSessionSerializer,
    GameRoundSerializer,
    PlayerAnswerSerializer,
    PlayerAnswerCreateSerializer,
    PlayerGameStatsSerializer,
    GameStartSerializer,
    GameResultsSerializer,
)
from .permissions import IsRoomHost, IsGameParticipant, CanAnswerQuestion
from apps.rooms.models import Room
from apps.questions.models import Quiz


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsRoomHost])
def start_game(request, room_id):
    """
    Запустить игру в комнате
    """
    room = get_object_or_404(Room, id=room_id)

    if room.host != request.user:
        raise PermissionDenied("Только хост комнаты может запустить игру")

    if room.status not in [Room.Status.DRAFT, Room.Status.OPEN]:
        return Response(
            {"error": "Комната недоступна для запуска игры"},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = GameStartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    quiz_id = serializer.validated_data['quiz_id']
    quiz = get_object_or_404(Quiz, id=quiz_id)

    active_session = GameSession.objects.filter(
        room=room,
        status__in=[GameSession.Status.WAITING, GameSession.Status.PLAYING, GameSession.Status.PAUSED]
    ).first()

    if active_session:
        return Response(
            {"error": "В этой комнате уже есть активная игровая сессия"},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        session = GameSession.objects.create(
            room=room,
            quiz=quiz,
            status=GameSession.Status.WAITING
        )

        # Создаем раунды для всех вопросов
        quiz_questions = quiz.quizquestion_set.select_related('question').order_by('order')

        for idx, qq in enumerate(quiz_questions, start=1):
            GameRound.objects.create(
                session=session,
                question=qq.question,
                round_number=idx,
                time_limit=30
            )

        participants = room.participants.select_related('user')
        for participant in participants:
            PlayerGameStats.objects.create(
                session=session,
                user=participant.user
            )

        room.status = Room.Status.IN_PROGRESS
        room.save(update_fields=['status'])

    return Response(
        GameSessionSerializer(session).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def get_session(request, session_id):
    """
    Получить информацию об игровой сессии
    """
    session = get_object_or_404(GameSession, id=session_id)

    if not session.room.participants.filter(user=request.user).exists():
        raise PermissionDenied("You are not a participant of this game")

    return Response(GameSessionSerializer(session).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def start_session(request, session_id):
    """
    Запустить игровую сессию (начать первый раунд)
    """
    session = get_object_or_404(GameSession, id=session_id)

    if session.room.host != request.user:
        raise PermissionDenied("Только хост комнаты может запустить сессию")

    if session.status != GameSession.Status.WAITING:
        return Response(
            {"error": f"Невозможно запустить сессию в статусе: {session.get_status_display()}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.start()

    first_round = session.rounds.filter(round_number=1).first()
    if first_round:
        first_round.start()

    return Response(GameSessionSerializer(session).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def pause_session(request, session_id):
    """
    Поставить игру на паузу
    """
    session = get_object_or_404(GameSession, id=session_id)

    if session.room.host != request.user:
        raise PermissionDenied("Только хост комнаты может поставить игру на паузу")

    if session.status != GameSession.Status.PLAYING:
        return Response(
            {"error": f"Невозможно поставить на паузу сессию в статусе: {session.get_status_display()}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.pause()

    return Response(GameSessionSerializer(session).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def resume_session(request, session_id):
    """
    Продолжить игру после паузы
    """
    session = get_object_or_404(GameSession, id=session_id)

    if session.room.host != request.user:
        raise PermissionDenied("Только хост комнаты может продолжить игру")

    if session.status != GameSession.Status.PAUSED:
        return Response(
            {"error": f"Невозможно продолжить сессию в статусе: {session.get_status_display()}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.resume()

    return Response(GameSessionSerializer(session).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def get_current_question(request, session_id):
    """
    Получить текущий вопрос
    """
    session = get_object_or_404(GameSession, id=session_id)

    if not session.room.participants.filter(user=request.user).exists():
        raise PermissionDenied("Вы не являетесь участником этой игры")

    if session.status not in [GameSession.Status.PLAYING, GameSession.Status.PAUSED]:
        return Response(
            {"error": "Игра не идёт"},
            status=status.HTTP_400_BAD_REQUEST
        )

    current_round = session.rounds.filter(
        round_number=session.current_question_index + 1
    ).first()

    if not current_round:
        return Response(
            {"error": "Текущий раунд не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(GameRoundSerializer(current_round).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_answer(request, session_id):
    """
    Отправить ответ на текущий вопрос
    """
    session = get_object_or_404(GameSession, id=session_id)

    if not session.room.participants.filter(user=request.user).exists():
        raise PermissionDenied("Вы не являетесь участником этой игры")

    if session.status != GameSession.Status.PLAYING:
        return Response(
            {"error": "Игра не идёт"},
            status=status.HTTP_400_BAD_REQUEST
        )

    current_round = session.rounds.filter(
        round_number=session.current_question_index + 1,
        status=GameRound.Status.ACTIVE
    ).first()

    if not current_round:
        return Response(
            {"error": "Активный раунд не найден"},
            status=status.HTTP_404_NOT_FOUND
        )

    if current_round.answers.filter(user=request.user).exists():
        return Response(
            {"error": "Вы уже ответили на этот вопрос"},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = PlayerAnswerCreateSerializer(
        data=request.data,
        context={
            'round': current_round,
            'round_id': current_round.id,
            'user': request.user
        }
    )
    serializer.is_valid(raise_exception=True)
    answer = serializer.save()

    total_participants = session.player_stats.count()
    total_answers = current_round.answers.count()

    should_advance = False

    if total_answers >= total_participants:
        should_advance = True

    if should_advance:
        current_round.complete()

        next_index = session.current_question_index + 1
        total_questions = session.quiz.questions.count()

        if next_index < total_questions:
            session.current_question_index = next_index
            session.save(update_fields=['current_question_index'])

            next_round = session.rounds.filter(round_number=next_index + 1).first()
            if next_round:
                next_round.start()
        else:
            session.finish()
            session.room.status = Room.Status.FINISHED
            session.room.save(update_fields=['status'])

            for stats in session.player_stats.all():
                stats.finalize()

            ranked_stats = session.player_stats.order_by('-total_points', 'completed_at')
            for rank, stats in enumerate(ranked_stats, start=1):
                stats.rank = rank
                stats.save(update_fields=['rank'])

            # Создаем записи в историю игр для всех участников
            from apps.users.models import GameHistory
            total_questions = session.quiz.questions.count()

            for stats in session.player_stats.all():
                GameHistory.objects.create(
                    user=stats.user,
                    session=session,
                    room=session.room,
                    quiz=session.quiz,
                    final_points=stats.total_points,
                    correct_answers=stats.correct_answers,
                    total_questions=total_questions,
                    final_rank=stats.rank
                )

    response_data = {
        'answer': PlayerAnswerSerializer(answer).data,
        'is_correct': answer.is_correct,
        'points_earned': answer.points_earned,
        'next_question': should_advance and session.status == GameSession.Status.PLAYING,
        'game_finished': session.status == GameSession.Status.FINISHED,
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsGameParticipant])
def get_results(request, session_id):
    """
    Получить результаты игры
    """
    session = get_object_or_404(GameSession, id=session_id)

    if not session.room.participants.filter(user=request.user).exists():
        raise PermissionDenied("Вы не являетесь участником этой игры")

    leaderboard = session.player_stats.select_related('user').order_by('-total_points', 'completed_at')

    total_rounds = session.rounds.count()
    completed_rounds = session.rounds.filter(status=GameRound.Status.COMPLETED).count()

    data = {
        'session': session,
        'leaderboard': leaderboard,
        'total_rounds': total_rounds,
        'completed_rounds': completed_rounds,
    }

    serializer = GameResultsSerializer(data)
    return Response(serializer.data)


class GameSessionListView(generics.ListAPIView):
    """
    Список игровых сессий пользователя
    """
    serializer_class = GameSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GameSession.objects.filter(
            player_stats__user=self.request.user
        ).select_related('room', 'quiz').order_by('-created_at')

