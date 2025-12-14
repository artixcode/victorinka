import pytest
from unittest.mock import Mock, MagicMock

from apps.game.infrastructure.event_bus import EventBus, EventHandler
from apps.game.domain.events import (
    DomainEvent,
    QuestionAnsweredEvent,
    GameStartedEvent,
    GameFinishedEvent
)


class MockEventHandler(EventHandler):
    """Мок-обработчик для тестов"""

    def __init__(self):
        self.handled_events = []
        self.call_count = 0

    def handle(self, event: DomainEvent) -> None:
        self.handled_events.append(event)
        self.call_count += 1


class AsyncMockEventHandler(EventHandler):
    """Мок-обработчик с поддержкой async"""

    def __init__(self):
        self.handled_events = []

    def handle(self, event: DomainEvent) -> None:
        self.handled_events.append(event)

    def can_handle_async(self) -> bool:
        return True


class TestEventBus:
    """Тесты для EventBus"""

    def setup_method(self):
        """Инициализация перед каждым тестом"""
        # Сбрасываем синглтон для изоляции тестов
        EventBus.reset_instance()
        self.event_bus = EventBus.get_instance()

    def teardown_method(self):
        """Очистка после каждого теста"""
        EventBus.reset_instance()

    # ============ Тесты Singleton паттерна ============

    def test_event_bus_is_singleton(self):
        """EventBus должен быть синглтоном"""
        bus1 = EventBus.get_instance()
        bus2 = EventBus.get_instance()

        assert bus1 is bus2

    def test_reset_instance(self):
        """reset_instance() должен сбрасывать синглтон"""
        bus1 = EventBus.get_instance()
        EventBus.reset_instance()
        bus2 = EventBus.get_instance()

        assert bus1 is not bus2

    # ============ Тесты подписки/отписки ============

    def test_subscribe_handler(self):
        """Подписка обработчика на событие"""
        handler = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        assert self.event_bus.get_handlers_count(QuestionAnsweredEvent) == 1

    def test_subscribe_multiple_handlers(self):
        """Подписка нескольких обработчиков на одно событие"""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler1)
        self.event_bus.subscribe(QuestionAnsweredEvent, handler2)

        assert self.event_bus.get_handlers_count(QuestionAnsweredEvent) == 2

    def test_subscribe_same_handler_twice(self):
        """Повторная подписка того же обработчика игнорируется"""
        handler = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler)
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        assert self.event_bus.get_handlers_count(QuestionAnsweredEvent) == 1

    def test_unsubscribe_handler(self):
        """Отписка обработчика от события"""
        handler = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler)
        self.event_bus.unsubscribe(QuestionAnsweredEvent, handler)

        assert self.event_bus.get_handlers_count(QuestionAnsweredEvent) == 0

    # ============ Тесты публикации событий ============

    def test_publish_event_calls_handler(self):
        """Публикация события должна вызывать обработчик"""
        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        event = QuestionAnsweredEvent(
            session_id=1,
            round_id=2,
            user_id=3,
            answer_id=4,
            is_correct=True,
            points_earned=15,
            time_taken=5.0,
            is_first_answer=True
        )

        self.event_bus.publish(event)

        assert handler.call_count == 1
        assert handler.handled_events[0] == event

    def test_publish_event_calls_multiple_handlers(self):
        """Публикация события вызывает всех подписанных обработчиков"""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler1)
        self.event_bus.subscribe(QuestionAnsweredEvent, handler2)

        event = QuestionAnsweredEvent(
            session_id=1,
            round_id=2,
            user_id=3,
            answer_id=4,
            is_correct=True,
            points_earned=15,
            time_taken=5.0,
            is_first_answer=False
        )

        self.event_bus.publish(event)

        assert handler1.call_count == 1
        assert handler2.call_count == 1

    def test_publish_event_without_handlers(self):
        """Публикация события без обработчиков не вызывает ошибку"""
        event = QuestionAnsweredEvent(
            session_id=1,
            round_id=2,
            user_id=3,
            answer_id=4,
            is_correct=True,
            points_earned=15,
            time_taken=5.0,
            is_first_answer=False
        )

        # Не должно быть исключения
        self.event_bus.publish(event)

    def test_publish_all_events(self):
        """Публикация нескольких событий"""
        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        events = [
            QuestionAnsweredEvent(
                session_id=1, round_id=i, user_id=1, answer_id=i,
                is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
            )
            for i in range(3)
        ]

        self.event_bus.publish_all(events)

        assert handler.call_count == 3

    # ============ Тесты обработки ошибок ============

    def test_handler_error_doesnt_stop_other_handlers(self):
        """Ошибка в одном обработчике не останавливает другие"""
        error_handler = MockEventHandler()
        error_handler.handle = Mock(side_effect=Exception("Test error"))

        good_handler = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, error_handler)
        self.event_bus.subscribe(QuestionAnsweredEvent, good_handler)

        event = QuestionAnsweredEvent(
            session_id=1, round_id=1, user_id=1, answer_id=1,
            is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
        )

        self.event_bus.publish(event)

        # good_handler должен был выполниться несмотря на ошибку в error_handler
        assert good_handler.call_count == 1

    # ============ Тесты enable/disable ============

    def test_disable_event_bus(self):
        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        self.event_bus.disable()

        event = QuestionAnsweredEvent(
            session_id=1, round_id=1, user_id=1, answer_id=1,
            is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
        )

        self.event_bus.publish(event)

        assert handler.call_count == 0

    def test_enable_event_bus(self):
        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        self.event_bus.disable()
        self.event_bus.enable()

        event = QuestionAnsweredEvent(
            session_id=1, round_id=1, user_id=1, answer_id=1,
            is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
        )

        self.event_bus.publish(event)

        assert handler.call_count == 1

    # ============ Тесты middleware ============

    def test_add_middleware(self):
        """Добавление middleware"""
        middleware_called = []

        def test_middleware(event):
            middleware_called.append(event)
            return event

        self.event_bus.add_middleware(test_middleware)

        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)

        event = QuestionAnsweredEvent(
            session_id=1, round_id=1, user_id=1, answer_id=1,
            is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
        )

        self.event_bus.publish(event)

        assert len(middleware_called) == 1
        assert middleware_called[0] == event

    # ============ Тесты утилит ============

    def test_clear_handlers(self):
        """Очистка всех обработчиков"""
        handler = MockEventHandler()
        self.event_bus.subscribe(QuestionAnsweredEvent, handler)
        self.event_bus.subscribe(GameStartedEvent, handler)

        self.event_bus.clear_handlers()

        assert self.event_bus.get_handlers_count(QuestionAnsweredEvent) == 0
        assert self.event_bus.get_handlers_count(GameStartedEvent) == 0

    def test_get_all_handlers(self):
        """Получение всех обработчиков"""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, handler1)
        self.event_bus.subscribe(GameStartedEvent, handler2)

        all_handlers = self.event_bus.get_all_handlers()

        assert QuestionAnsweredEvent in all_handlers
        assert GameStartedEvent in all_handlers
        assert len(all_handlers[QuestionAnsweredEvent]) == 1
        assert len(all_handlers[GameStartedEvent]) == 1

    # ============ Интеграционные тесты ============

    def test_multiple_event_types(self):
        """Обработка разных типов событий"""
        question_handler = MockEventHandler()
        game_handler = MockEventHandler()

        self.event_bus.subscribe(QuestionAnsweredEvent, question_handler)
        self.event_bus.subscribe(GameStartedEvent, game_handler)

        question_event = QuestionAnsweredEvent(
            session_id=1, round_id=1, user_id=1, answer_id=1,
            is_correct=True, points_earned=10, time_taken=5.0, is_first_answer=False
        )

        game_event = GameStartedEvent(
            session_id=1,
            room_id=1,
            quiz_id=1,
            host_id=1,
            participants_count=2
        )

        self.event_bus.publish(question_event)
        self.event_bus.publish(game_event)

        assert question_handler.call_count == 1
        assert game_handler.call_count == 1
        assert question_handler.handled_events[0] == question_event
        assert game_handler.handled_events[0] == game_event

