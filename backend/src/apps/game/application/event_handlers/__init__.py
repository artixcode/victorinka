import logging
from typing import Optional

from apps.game.domain.events import (
    QuestionAnsweredEvent,
    GameStartedEvent,
    GameFinishedEvent,
    RoundCompletedEvent,
)
from apps.game.infrastructure.event_bus import EventHandler
from apps.game.models import PlayerGameStats, GameSession
from apps.users.models import User, GameHistory

logger = logging.getLogger(__name__)


class UpdatePlayerStatsOnAnswerHandler(EventHandler):
    """
    Обработчик: обновление статистики игрока при ответе на вопрос.
    """

    def handle(self, event: QuestionAnsweredEvent) -> None:
        """
        Обновить статистику игрока.
        """
        try:
            stats = PlayerGameStats.objects.get(
                session_id=event.session_id,
                user_id=event.user_id
            )

            # Обновление счётчиков
            if event.is_correct:
                stats.correct_answers += 1
            else:
                stats.wrong_answers += 1

            # Обновление очков
            stats.total_points += event.points_earned

            stats.save(update_fields=['total_points', 'correct_answers', 'wrong_answers'])

            logger.info(
                f"Updated stats for user {event.user_id} in session {event.session_id}: "
                f"+{event.points_earned} points (total: {stats.total_points})"
            )

        except PlayerGameStats.DoesNotExist:
            logger.error(
                f"PlayerGameStats not found for user {event.user_id} "
                f"in session {event.session_id}"
            )
        except Exception as e:
            logger.error(
                f"Error updating player stats: {e}",
                exc_info=True
            )


class UpdateGlobalUserStatsOnAnswerHandler(EventHandler):
    """
    Обработчик: обновление глобальной статистики пользователя.
    """

    def handle(self, event: QuestionAnsweredEvent) -> None:
        """
        Обновить глобальную статистику пользователя.
        """
        try:
            user = User.objects.get(id=event.user_id)

            # Добавляем очки к общему счёту пользователя
            user.add_points(event.points_earned)
            user.save(update_fields=['total_points'])

            logger.info(
                f"Updated global stats for user {event.user_id}: "
                f"+{event.points_earned} points (total: {user.total_points})"
            )

        except User.DoesNotExist:
            logger.error(f"User {event.user_id} not found")
        except Exception as e:
            logger.error(
                f"Error updating global user stats: {e}",
                exc_info=True
            )

    def can_handle_async(self) -> bool:
        """
        Этот обработчик может быть асинхронным.
        """
        return True


class SaveGameHistoryOnFinishHandler(EventHandler):
    """
    Обработчик: сохранение игры в историю пользователя.
    """

    def handle(self, event: GameFinishedEvent) -> None:
        """
        Сохранить игру в историю.
        """
        try:
            session = GameSession.objects.get(id=event.session_id)

            # Получаем статистику всех игроков
            player_stats = PlayerGameStats.objects.filter(
                session_id=event.session_id
            ).select_related('user')

            # Определяем места игроков (ранжирование по очкам)
            sorted_stats = sorted(
                player_stats,
                key=lambda s: s.total_points,
                reverse=True
            )

            # Назначаем ранги
            for rank, stats in enumerate(sorted_stats, start=1):
                stats.rank = rank
                stats.finalize()
                stats.save(update_fields=['rank', 'completed_at'])

            # Сохраняем в историю для каждого игрока
            for stats in player_stats:
                GameHistory.objects.create(
                    user=stats.user,
                    session=session,
                    room=session.room,
                    quiz=session.quiz,
                    final_points=stats.total_points,
                    correct_answers=stats.correct_answers,
                    total_questions=stats.correct_answers + stats.wrong_answers,
                    final_rank=stats.rank
                )

                logger.info(
                    f"Saved game history for user {stats.user_id}: "
                    f"rank {stats.rank}, {stats.total_points} points"
                )

            # Обновляем счётчик побед у победителя
            if event.winner_id:
                winner = User.objects.get(id=event.winner_id)
                winner.total_wins += 1
                winner.save(update_fields=['total_wins'])

                logger.info(f"User {event.winner_id} won the game! Total wins: {winner.total_wins}")

        except GameSession.DoesNotExist:
            logger.error(f"GameSession {event.session_id} not found")
        except Exception as e:
            logger.error(
                f"Error saving game history: {e}",
                exc_info=True
            )

    def can_handle_async(self) -> bool:
        return True


class LogGameEventsHandler(EventHandler):
    """
    Обработчик: логирование всех игровых событий.
    """

    def handle(self, event) -> None:
        """
        Залогировать событие.
        """
        logger.info(
            f"[GAME EVENT] {event.__class__.__name__}: "
            f"{self._format_event(event)}"
        )

    def _format_event(self, event) -> str:
        """
        Форматировать событие для лога.
        """
        # Получаем все поля события кроме occurred_at
        fields = {
            k: v for k, v in event.__dict__.items()
            if k != 'occurred_at'
        }
        return str(fields)


class NotifyPlayersHandler(EventHandler):
    """
    Обработчик: отправка уведомлений игрокам через WebSocket.

    TODO: Реализовать после подключения Django Channels.

    Будет отправлять уведомления о:
    - Начале игры
    - Новом вопросе
    - Ответах других игроков
    - Завершении игры
    """

    def handle(self, event) -> None:
        """
        Отправить уведомление через WebSocket.
        """
        # TODO: Реализовать после подключения WebSocket
        logger.debug(f"[WebSocket] Would send notification for: {event.__class__.__name__}")

    def can_handle_async(self) -> bool:
        """WebSocket уведомления лучше отправлять асинхронно"""
        return True

