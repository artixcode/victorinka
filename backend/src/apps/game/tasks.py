import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def start_round_timer(self, session_id: int, room_id: int, round_number: int, duration_seconds: int):
    """
    Запустить таймер раунда с отправкой обновлений каждую секунду.
    """
    from apps.game.infrastructure.redis_game_state_repository import game_state_repository
    from apps.game.application.services.game_coordinator_service import GameCoordinatorService

    channel_layer = get_channel_layer()
    room_group_name = f"game_room_{room_id}"

    logger.info(f"Начинаю таймер для раунда {round_number} в сессии {session_id}, длительность: {duration_seconds}с")

    start_time = time.time()
    total_paused_duration = 0

    try:
        for remaining in range(duration_seconds, 0, -1):
            # Проверяем состояние игры
            game_state = game_state_repository.get_game_state(session_id)

            if game_state and game_state.get('status') == 'paused':
                pause_start_time = time.time()
                logger.info(f"Игра на паузе, таймер раунда {round_number} приостановлен (осталось {remaining}с)")

                try:
                    async_to_sync(channel_layer.group_send)(
                        room_group_name,
                        {
                            'type': 'timer.paused',
                            'session_id': session_id,
                            'round_number': round_number,
                            'paused_at_seconds': remaining
                        }
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки timer_paused: {e}")

                # Ждем возобновления
                while True:
                    time.sleep(1)
                    game_state = game_state_repository.get_game_state(session_id)

                    # Проверяем, не завершен ли раунд во время паузы
                    round_data = game_state_repository.get_round_data(session_id, round_number)
                    if round_data and round_data.get('status') == 'completed':
                        logger.info(f"Раунд {round_number} завершен во время паузы")
                        return

                    # Если игра возобновлена
                    if game_state and game_state.get('status') != 'paused':
                        pause_duration = time.time() - pause_start_time
                        total_paused_duration += pause_duration
                        logger.info(f"Игра возобновлена после {pause_duration:.1f}с паузы (осталось {remaining}с)")

                        try:
                            async_to_sync(channel_layer.group_send)(
                                room_group_name,
                                {
                                    'type': 'timer.resumed',
                                    'session_id': session_id,
                                    'round_number': round_number,
                                    'remaining_seconds': remaining,
                                    'pause_duration': round(pause_duration, 1)
                                }
                            )
                        except Exception as e:
                            logger.error(f"Ошибка отправки timer_resumed: {e}")

                        break

            round_data = game_state_repository.get_round_data(session_id, round_number)
            if round_data and round_data.get('status') == 'completed':
                logger.info(f"Раунд {round_number} завершен досрочно, останавливаю таймер")
                return

            event_data = {
                'type': 'timer.update',
                'session_id': session_id,
                'round_number': round_number,
                'remaining_seconds': remaining,
                'total_seconds': duration_seconds
            }

            try:
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    event_data
                )

                if remaining == duration_seconds or remaining % 10 == 0 or remaining <= 5:
                    logger.info(f"Таймер раунда {round_number}: осталось {remaining}с")
            except Exception as e:
                logger.error(f"Ошибка отправки timer_update: {e}")

            elapsed = time.time() - start_time - total_paused_duration
            target_elapsed = duration_seconds - remaining + 1
            sleep_time = target_elapsed - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)

        logger.info(f"Время раунда {round_number} истекло, автозавершение...")

        coordinator = GameCoordinatorService()
        result = coordinator.auto_complete_round(session_id, round_number, reason='time_expired')

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'round.ended',
                'session_id': session_id,
                'round_number': round_number,
                'reason': 'time_expired',
                'message': 'Время вышло!'
            }
        )

        if result and result.get('has_next') and result.get('next_question_data'):
            next_q = result['next_question_data']
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'new.question',
                    'session_id': session_id,
                    'round_number': next_q.get('round_number'),
                    'question_id': next_q.get('question_id'),
                    'question_text': next_q.get('question_text'),
                    'options': next_q.get('options', []),
                    'total_questions': next_q.get('total_questions'),
                    'timer_duration': next_q.get('timer_duration', 30)
                }
            )
            logger.info(f"Отправлен новый вопрос #{next_q.get('round_number')} после автозавершения")

        elif result and not result.get('has_next'):
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'game.finished',
                    'session_id': session_id,
                    'message': 'Игра завершена!'
                }
            )
            logger.info(f" Игра {session_id} завершена, отправлено событие game_finished")

        logger.info(f"Таймер раунда {round_number} завершен успешно")

    except Exception as e:
        logger.error(f"Ошибка в таймере раунда {round_number}: {e}", exc_info=True)
        raise


@shared_task
def cleanup_old_game_sessions():

    from apps.game.models import GameSession
    from apps.game.infrastructure.redis_game_state_repository import game_state_repository
    from datetime import timedelta

    logger.info("Начинаю очистку старых игровых сессий из Redis...")

    cutoff_time = timezone.now() - timedelta(hours=24)
    old_sessions = GameSession.objects.filter(
        status=GameSession.Status.FINISHED,
        finished_at__lt=cutoff_time
    )

    cleaned_count = 0
    for session in old_sessions:
        try:
            game_state_repository.clear_session(session.id)
            cleaned_count += 1
        except Exception as e:
            logger.error(f"Ошибка при очистке сессии {session.id}: {e}")

    logger.info(f"Очищено {cleaned_count} старых сессий из Redis")
    return cleaned_count


@shared_task
def notify_inactive_players():
    from apps.game.models import GameSession
    from datetime import timedelta

    logger.info("Проверка неактивных игровых сессий...")

    cutoff_time = timezone.now() - timedelta(minutes=30)
    inactive_sessions = GameSession.objects.filter(
        status=GameSession.Status.WAITING,
        created_at__lt=cutoff_time
    ).select_related('room', 'quiz')

    channel_layer = get_channel_layer()

    notified_count = 0
    for session in inactive_sessions:
        room_group_name = f"room_{session.room_id}"

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'system.message',
                'message': f'Игра "{session.quiz.title}" ожидает начала уже более 30 минут. Начните игру или покиньте комнату.',
                'level': 'warning'
            }
        )

        notified_count += 1

    logger.info(f"Отправлено {notified_count} уведомлений о неактивности")
    return notified_count

