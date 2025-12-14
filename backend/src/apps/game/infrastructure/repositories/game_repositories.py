from typing import List, Optional

from apps.game.models import GameSession, GameRound, PlayerGameStats, PlayerAnswer
from apps.game.domain.repositories import (
    IGameSessionRepository,
    IGameRoundRepository,
    IPlayerGameStatsRepository,
    IPlayerAnswerRepository,
    EntityNotFoundException,
)


class GameSessionRepository(IGameSessionRepository):
    def get_by_id(self, session_id: int) -> GameSession:
        """
        Получить сессию по ID.
        """
        try:
            return GameSession.objects.select_related(
                'room',
                'quiz'
            ).prefetch_related(
                'rounds',
                'player_stats__user'
            ).get(id=session_id)
        except GameSession.DoesNotExist:
            raise EntityNotFoundException("GameSession", session_id)

    def save(self, session: GameSession) -> GameSession:
        """Сохранить сессию."""
        session.save()
        return session

    def get_active_sessions_for_room(self, room_id: int) -> List[GameSession]:
        """
        Получить активные сессии для комнаты.
        """
        return list(
            GameSession.objects.filter(
                room_id=room_id,
                status__in=[
                    GameSession.Status.WAITING,
                    GameSession.Status.PLAYING,
                    GameSession.Status.PAUSED
                ]
            ).select_related('room', 'quiz')
        )

    def find_by_room_and_status(
        self,
        room_id: int,
        statuses: List[str]
    ) -> Optional[GameSession]:
        """
        Найти первую сессию по комнате и статусам.
        """
        return GameSession.objects.filter(
            room_id=room_id,
            status__in=statuses
        ).select_related('room', 'quiz').first()

    def create(
        self,
        room_id: int,
        quiz_id: int,
        status: str = None
    ) -> GameSession:
        """
        Создать новую игровую сессию.
        """
        if status is None:
            status = GameSession.Status.WAITING

        return GameSession.objects.create(
            room_id=room_id,
            quiz_id=quiz_id,
            status=status
        )


class GameRoundRepository(IGameRoundRepository):

    def get_by_id(self, round_id: int) -> GameRound:
        """Получить раунд по ID"""
        try:
            return GameRound.objects.select_related(
                'session',
                'question'
            ).prefetch_related(
                'answers__user'
            ).get(id=round_id)
        except GameRound.DoesNotExist:
            raise EntityNotFoundException("GameRound", round_id)

    def save(self, round_obj: GameRound) -> GameRound:
        """Сохранить раунд."""
        round_obj.save()
        return round_obj

    def get_rounds_for_session(self, session_id: int) -> List[GameRound]:
        """
        Получить все раунды для сессии, упорядоченные по номеру.
        """
        return list(
            GameRound.objects.filter(
                session_id=session_id
            ).select_related('question').order_by('round_number')
        )

    def get_current_round(
        self,
        session_id: int,
        round_number: int
    ) -> Optional[GameRound]:
        """
        Получить текущий раунд.
        """
        return GameRound.objects.filter(
            session_id=session_id,
            round_number=round_number
        ).select_related('session', 'question').first()

    def bulk_create(self, rounds: List[GameRound]) -> List[GameRound]:
        """
        Массово создать раунды.
        """
        return GameRound.objects.bulk_create(rounds)


class PlayerGameStatsRepository(IPlayerGameStatsRepository):

    def get_by_session_and_user(
        self,
        session_id: int,
        user_id: int
    ) -> PlayerGameStats:
        """Получить статистику игрока в сессии."""
        try:
            return PlayerGameStats.objects.select_related(
                'session',
                'user'
            ).get(
                session_id=session_id,
                user_id=user_id
            )
        except PlayerGameStats.DoesNotExist:
            raise EntityNotFoundException(
                "PlayerGameStats",
                f"session={session_id}, user={user_id}"
            )

    def save(self, stats: PlayerGameStats) -> PlayerGameStats:
        """Сохранить статистику."""
        stats.save()
        return stats

    def get_all_for_session(self, session_id: int) -> List[PlayerGameStats]:
        """Получить статистику всех игроков в сессии."""
        return list(
            PlayerGameStats.objects.filter(
                session_id=session_id
            ).select_related('user')
        )

    def get_leaderboard(self, session_id: int) -> List[PlayerGameStats]:
        """
        Получить таблицу лидеров для сессии.

        Сортировка:
        1. По убыванию очков
        2. При равных очках - по времени завершения (раньше = выше)
        """
        return list(
            PlayerGameStats.objects.filter(
                session_id=session_id
            ).select_related('user').order_by(
                '-total_points',
                'completed_at'
            )
        )

    def bulk_create(self, stats_list: List[PlayerGameStats]) -> List[PlayerGameStats]:
        """Массово создать статистику."""
        return PlayerGameStats.objects.bulk_create(stats_list)

    def create(self, session_id: int, user_id: int) -> PlayerGameStats:
        """
        Создать статистику для игрока.
        """
        return PlayerGameStats.objects.create(
            session_id=session_id,
            user_id=user_id
        )


class PlayerAnswerRepository(IPlayerAnswerRepository):

    def get_by_id(self, answer_id: int) -> PlayerAnswer:
        """Получить ответ по ID."""
        try:
            return PlayerAnswer.objects.select_related(
                'round',
                'user',
                'selected_option'
            ).get(id=answer_id)
        except PlayerAnswer.DoesNotExist:
            raise EntityNotFoundException("PlayerAnswer", answer_id)

    def save(self, answer: PlayerAnswer) -> PlayerAnswer:
        """Сохранить ответ."""
        answer.save()
        return answer

    def get_answers_for_round(self, round_id: int) -> List[PlayerAnswer]:
        """
        Получить все ответы для раунда.

        Сортировка по времени ответа (первый = самый быстрый).
        """
        return list(
            PlayerAnswer.objects.filter(
                round_id=round_id
            ).select_related(
                'user',
                'selected_option'
            ).order_by('answered_at')
        )

    def has_user_answered(self, round_id: int, user_id: int) -> bool:
        """
        Проверить, ответил ли пользователь на раунд.
        """
        return PlayerAnswer.objects.filter(
            round_id=round_id,
            user_id=user_id
        ).exists()

    def get_user_answer(
        self,
        round_id: int,
        user_id: int
    ) -> Optional[PlayerAnswer]:
        """Получить ответ пользователя на раунд."""
        return PlayerAnswer.objects.filter(
            round_id=round_id,
            user_id=user_id
        ).select_related('selected_option').first()

    def create(
        self,
        round_id: int,
        user_id: int,
        selected_option_id: int,
        time_taken: float
    ) -> PlayerAnswer:
        """
        Создать новый ответ.
        """
        from apps.questions.models import AnswerOption

        option = AnswerOption.objects.get(id=selected_option_id)

        return PlayerAnswer(
            round_id=round_id,
            user_id=user_id,
            selected_option=option,
            is_correct=option.is_correct,
            time_taken=time_taken
        )

