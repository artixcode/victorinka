from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RoundTimerService:

    DEFAULT_TIMER_DURATION = 30
    MIN_TIMER_DURATION = 5
    MAX_TIMER_DURATION = 300

    def __init__(self, redis_repository):
        self.repository = redis_repository

    def calculate_round_duration(self, question_difficulty: str, custom_duration: Optional[int] = None) -> int:
        """
        Рассчитать длительность раунда на основе сложности вопроса.
        """
        if custom_duration is not None:
            if self.MIN_TIMER_DURATION <= custom_duration <= self.MAX_TIMER_DURATION:
                return custom_duration
            else:
                logger.warning(
                    f"Некорректная длительность {custom_duration}с, использую значение по умолчанию"
                )

        # Автоматический расчет по сложности
        duration_map = {
            'easy': 15,
            'medium': 30,
            'hard': 60
        }

        return duration_map.get(question_difficulty, self.DEFAULT_TIMER_DURATION)

    def start_timer(
        self,
        session_id: int,
        round_number: int,
        duration_seconds: int
    ) -> dict:
        """
        Начать таймер для раунда.
        """
        if duration_seconds < self.MIN_TIMER_DURATION:
            raise ValueError(f"Длительность таймера не может быть меньше {self.MIN_TIMER_DURATION}с")

        if duration_seconds > self.MAX_TIMER_DURATION:
            raise ValueError(f"Длительность таймера не может быть больше {self.MAX_TIMER_DURATION}с")

        timer_data = {
            'duration': duration_seconds,
            'started_at': None,
            'status': 'running'
        }

        round_data = self.repository.get_round_data(session_id, round_number)
        if round_data:
            round_data['timer'] = timer_data
            self.repository.set_current_round(session_id, round_number, round_data)

        logger.info(f"Таймер запущен для раунда {round_number}, длительность: {duration_seconds}с")

        return {
            'type': 'timer_started',
            'session_id': session_id,
            'round_number': round_number,
            'duration_seconds': duration_seconds
        }

    def stop_timer(self, session_id: int, round_number: int, reason: str = 'manual') -> dict:
        """
        Остановить таймер раунда досрочно.
        """
        round_data = self.repository.get_round_data(session_id, round_number)

        if round_data and 'timer' in round_data:
            round_data['timer']['status'] = 'stopped'
            round_data['timer']['stopped_reason'] = reason
            self.repository.set_current_round(session_id, round_number, round_data)

        logger.info(f"⏸Таймер остановлен для раунда {round_number}, причина: {reason}")

        return {
            'type': 'timer_stopped',
            'session_id': session_id,
            'round_number': round_number,
            'reason': reason
        }

    def is_timer_active(self, session_id: int, round_number: int) -> bool:
        """
        Проверить, активен ли таймер для раунда.
        """
        round_data = self.repository.get_round_data(session_id, round_number)

        if not round_data or 'timer' not in round_data:
            return False

        timer = round_data['timer']
        return timer.get('status') == 'running'

    def get_remaining_time(self, session_id: int, round_number: int) -> Optional[int]:
        """
        Получить оставшееся время раунда
        """

        if not self.is_timer_active(session_id, round_number):
            return None

        round_data = self.repository.get_round_data(session_id, round_number)
        if round_data and 'timer' in round_data:
            return round_data['timer'].get('duration')

        return None

    def should_auto_complete_round(
        self,
        session_id: int,
        round_number: int,
        total_players: int
    ) -> bool:
        """
        Проверить, нужно ли автоматически завершить раунд.
        """
        # Проверяем количество ответов
        answers_count = self.repository.get_round_answers_count(session_id, round_number)

        if answers_count >= total_players:
            logger.info(f"Все {total_players} игрока ответили на раунд {round_number}")
            return True

        # Проверяем статус таймера
        if not self.is_timer_active(session_id, round_number):
            # Таймер остановлен или истек
            round_data = self.repository.get_round_data(session_id, round_number)
            if round_data and round_data.get('timer', {}).get('stopped_reason') == 'time_expired':
                logger.info(f"Время раунда {round_number} истекло")
                return True

        return False

    def extend_timer(
        self,
        session_id: int,
        round_number: int,
        additional_seconds: int
    ) -> dict:
        if additional_seconds < 0 or additional_seconds > 60:
            raise ValueError("Можно продлить не более чем на 60 секунд")

        round_data = self.repository.get_round_data(session_id, round_number)

        if not round_data or 'timer' not in round_data:
            raise ValueError("Таймер не найден")

        timer = round_data['timer']
        if timer.get('status') != 'running':
            raise ValueError("Таймер не активен")

        old_duration = timer['duration']
        new_duration = old_duration + additional_seconds

        timer['duration'] = new_duration
        timer['extended'] = True
        timer['extension_seconds'] = additional_seconds

        round_data['timer'] = timer
        self.repository.set_current_round(session_id, round_number, round_data)

        logger.info(f"Таймер раунда {round_number} продлен на {additional_seconds}с ({old_duration}→{new_duration})")

        return {
            'type': 'timer_extended',
            'session_id': session_id,
            'round_number': round_number,
            'additional_seconds': additional_seconds,
            'new_duration': new_duration
        }

