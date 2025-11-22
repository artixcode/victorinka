import logging

from apps.game.infrastructure.event_bus import event_bus
from apps.game.domain.events import (
    QuestionAnsweredEvent,
    GameStartedEvent,
    GameFinishedEvent,
    RoundStartedEvent,
    RoundCompletedEvent,
    GamePausedEvent,
    GameResumedEvent,
)
from apps.game.application.event_handlers import (
    UpdatePlayerStatsOnAnswerHandler,
    UpdateGlobalUserStatsOnAnswerHandler,
    SaveGameHistoryOnFinishHandler,
    LogGameEventsHandler,
    NotifyPlayersHandler,
)

logger = logging.getLogger(__name__)


def setup_event_handlers() -> None:
    """
    Зарегистрировать все event handlers.
    """

    # Когда игрок отвечает на вопрос

    # 1. Обновить статистику игрока в этой сессии
    event_bus.subscribe(
        QuestionAnsweredEvent,
        UpdatePlayerStatsOnAnswerHandler()
    )

    # 2. Обновить глобальную статистику пользователя
    event_bus.subscribe(
        QuestionAnsweredEvent,
        UpdateGlobalUserStatsOnAnswerHandler()
    )

    # Когда игра завершается

    # 1. Сохранить игру в историю
    event_bus.subscribe(
        GameFinishedEvent,
        SaveGameHistoryOnFinishHandler()
    )

    # Логирование всех событий

    log_handler = LogGameEventsHandler()
    event_bus.subscribe(GameStartedEvent, log_handler)
    event_bus.subscribe(QuestionAnsweredEvent, log_handler)
    event_bus.subscribe(GameFinishedEvent, log_handler)
    event_bus.subscribe(RoundStartedEvent, log_handler)
    event_bus.subscribe(RoundCompletedEvent, log_handler)
    event_bus.subscribe(GamePausedEvent, log_handler)
    event_bus.subscribe(GameResumedEvent, log_handler)

    # ========== WebSocket уведомления ==========
    # TODO: Включить после подключения Django Channels

    # notify_handler = NotifyPlayersHandler()
    # event_bus.subscribe(GameStartedEvent, notify_handler)
    # event_bus.subscribe(RoundStartedEvent, notify_handler)
    # event_bus.subscribe(QuestionAnsweredEvent, notify_handler)
    # event_bus.subscribe(GameFinishedEvent, notify_handler)

    logger.info("✅ Event handlers registered successfully")
    logger.info(f"📊 Total handlers: {_count_all_handlers()}")


def _count_all_handlers() -> int:
    """
    Подсчитать общее количество зарегистрированных обработчиков.
    """
    all_handlers = event_bus.get_all_handlers()
    return sum(len(handlers) for handlers in all_handlers.values())

