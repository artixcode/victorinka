from typing import Dict, List, Type, Callable, Any
from collections import defaultdict
import logging

from apps.game.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Базовый класс для обработчиков событий.
    """

    def handle(self, event: DomainEvent) -> None:
        """
        Обработать доменное событие.
        """
        raise NotImplementedError("Subclasses must implement handle() method")

    def can_handle_async(self) -> bool:
        """
        Может ли этот обработчик выполняться асинхронно.
        """
        return False


class EventBus:
    """
    для публикации и обработки доменных событий
    """

    _instance = None

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = defaultdict(list)
        self._middlewares: List[Callable] = []
        self._is_enabled = True

    @classmethod
    def get_instance(cls) -> 'EventBus':
        """
        Получить единственный экземпляр EventBus (Singleton).
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Сбросить синглтон (для тестов).
        """
        cls._instance = None

    def subscribe(
        self,
        event_class: Type[DomainEvent],
        handler: EventHandler
    ) -> None:
        """
        Подписать обработчик на событие.
        """
        if handler not in self._handlers[event_class]:
            self._handlers[event_class].append(handler)
            logger.debug(
                f"Handler {handler.__class__.__name__} subscribed to {event_class.__name__}"
            )

    def unsubscribe(
        self,
        event_class: Type[DomainEvent],
        handler: EventHandler
    ) -> None:
        """
        Отписать обработчик от события.
        """
        if handler in self._handlers[event_class]:
            self._handlers[event_class].remove(handler)
            logger.debug(
                f"Handler {handler.__class__.__name__} unsubscribed from {event_class.__name__}"
            )

    def publish(self, event: DomainEvent) -> None:
        """
        Опубликовать событие.
        """
        if not self._is_enabled:
            logger.debug(f"EventBus disabled, skipping event: {event}")
            return

        event_class = type(event)
        handlers = self._handlers.get(event_class, [])

        if not handlers:
            logger.debug(f"No handlers for event: {event_class.__name__}")
            return

        logger.info(f"Publishing event: {event_class.__name__} with {len(handlers)} handlers")

        processed_event = self._apply_middlewares(event)

        # Вызов всех обработчиков
        for handler in handlers:
            try:
                if handler.can_handle_async():
                    # Асинхронная обработка через Celery (будет реализовано позже)
                    self._handle_async(handler, processed_event)
                else:
                    # Синхронная обработка
                    handler.handle(processed_event)
                    logger.debug(
                        f"Handler {handler.__class__.__name__} processed {event_class.__name__}"
                    )
            except Exception as e:
                # Не прерываем обработку других handlers при ошибке
                logger.error(
                    f"Error in handler {handler.__class__.__name__} "
                    f"for event {event_class.__name__}: {e}",
                    exc_info=True
                )

    def publish_all(self, events: List[DomainEvent]) -> None:
        """
        Опубликовать несколько событий.
        """
        for event in events:
            self.publish(event)

    def add_middleware(self, middleware: Callable[[DomainEvent], DomainEvent]) -> None:
        """
        Добавить middleware для обработки событий.
        """
        self._middlewares.append(middleware)

    def _apply_middlewares(self, event: DomainEvent) -> DomainEvent:
        """
        Применить все middleware к событию.
        """
        result = event
        for middleware in self._middlewares:
            try:
                result = middleware(result)
            except Exception as e:
                logger.error(f"Error in middleware: {e}", exc_info=True)
        return result

    def _handle_async(self, handler: EventHandler, event: DomainEvent) -> None:
        """
        Асинхронная обработка события через Celery.

        TODO: Реализовать после подключения Celery.
        """
        logger.warning(
            f"Async handling not implemented yet. "
            f"Falling back to sync for {handler.__class__.__name__}"
        )
        handler.handle(event)

    def disable(self) -> None:
        self._is_enabled = False
        logger.info("EventBus disabled")

    def enable(self) -> None:
        self._is_enabled = True
        logger.info("EventBus enabled")

    def clear_handlers(self) -> None:
        """
        Очистить все обработчики.(тесты)
        """
        self._handlers.clear()
        logger.info("All handlers cleared")

    def get_handlers_count(self, event_class: Type[DomainEvent]) -> int:
        """
        Получить количество обработчиков для события.
        """
        return len(self._handlers.get(event_class, []))

    def get_all_handlers(self) -> Dict[Type[DomainEvent], List[EventHandler]]:
        """
        Получить все зарегистрированные обработчики.
        """
        return dict(self._handlers)


event_bus = EventBus.get_instance()

