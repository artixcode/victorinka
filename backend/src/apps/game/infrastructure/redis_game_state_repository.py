import json
from typing import List, Optional, Dict, Any
from django.core.cache import cache
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class RedisGameStateRepository:
    """
    Хранение состояния игровой сессии в Redis для real-time синхронизации.
    """

    # Шаблоны ключей
    STATE_KEY_TEMPLATE = "game:session:{id}:state"
    CURRENT_KEY_TEMPLATE = "game:session:{id}:current"
    ROUND_KEY_TEMPLATE = "game:session:{id}:round:{num}"
    ANSWERS_KEY_TEMPLATE = "game:session:{id}:answers:{round}"
    SCORES_KEY_TEMPLATE = "game:session:{id}:scores"
    PROGRESS_KEY_TEMPLATE = "game:session:{id}:progress"

    # Настройки
    TTL = 3600 * 48
    MAX_QUESTIONS = 1000

    def _get_state_key(self, session_id: int) -> str:
        return self.STATE_KEY_TEMPLATE.format(id=session_id)

    def _get_current_key(self, session_id: int) -> str:
        return self.CURRENT_KEY_TEMPLATE.format(id=session_id)

    def _get_round_key(self, session_id: int, round_number: int) -> str:
        return self.ROUND_KEY_TEMPLATE.format(id=session_id, num=round_number)

    def _get_answers_key(self, session_id: int, round_number: int) -> str:
        return self.ANSWERS_KEY_TEMPLATE.format(id=session_id, round=round_number)

    def _get_scores_key(self, session_id: int) -> str:
        return self.SCORES_KEY_TEMPLATE.format(id=session_id)

    def _get_progress_key(self, session_id: int) -> str:
        return self.PROGRESS_KEY_TEMPLATE.format(id=session_id)

    def save_game_state(self, session_id: int, state_data: dict) -> None:
        """
        Сохранить общее состояние игровой сессии.
        """
        key = self._get_state_key(session_id)
        state_data['updated_at'] = timezone.now().isoformat()
        cache.set(key, json.dumps(state_data), timeout=self.TTL)
        logger.info(f"💾 Saved game state for session {session_id}: {state_data.get('status')}")

    def get_game_state(self, session_id: int) -> Optional[dict]:
        """Получить общее состояние сессии."""
        key = self._get_state_key(session_id)
        state_json = cache.get(key)

        if not state_json:
            return None

        try:
            return json.loads(state_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse game state for session {session_id}")
            return None

    def update_session_status(self, session_id: int, status: str) -> None:
        """Обновить статус сессии (waiting/playing/paused/finished)."""
        state = self.get_game_state(session_id)
        if state:
            state['status'] = status
            state['updated_at'] = timezone.now().isoformat()
            key = self._get_state_key(session_id)
            cache.set(key, json.dumps(state), timeout=self.TTL)
            logger.info(f"Updated session {session_id} status to: {status}")

    def session_exists(self, session_id: int) -> bool:
        """Проверить существование сессии в Redis."""
        key = self._get_state_key(session_id)
        return cache.get(key) is not None


    def set_current_round(self, session_id: int, round_number: int, question_data: dict) -> None:
        """
        Установить текущий активный раунд.
        """
        current_key = self._get_current_key(session_id)
        round_key = self._get_round_key(session_id, round_number)

        # Сохраняем как текущий раунд
        cache.set(current_key, json.dumps(question_data), timeout=self.TTL)

        # Сохраняем полные данные раунда
        cache.set(round_key, json.dumps(question_data), timeout=self.TTL)

        # Обновляем прогресс
        self._update_progress(session_id, round_number)

        logger.info(f"Set current round {round_number} for session {session_id}")

    def get_current_round(self, session_id: int) -> Optional[dict]:
        """Получить данные текущего активного раунда."""
        key = self._get_current_key(session_id)
        round_json = cache.get(key)

        if not round_json:
            return None

        try:
            return json.loads(round_json)
        except json.JSONDecodeError:
            return None

    def get_round_data(self, session_id: int, round_number: int) -> Optional[dict]:
        """Получить данные конкретного раунда."""
        key = self._get_round_key(session_id, round_number)
        round_json = cache.get(key)

        if not round_json:
            return None

        try:
            return json.loads(round_json)
        except json.JSONDecodeError:
            return None

    def complete_round(self, session_id: int, round_number: int) -> None:
        """Пометить раунд как завершенный."""
        round_data = self.get_round_data(session_id, round_number)
        if round_data:
            round_data['status'] = 'completed'
            round_data['completed_at'] = timezone.now().isoformat()
            key = self._get_round_key(session_id, round_number)
            cache.set(key, json.dumps(round_data), timeout=self.TTL)
            logger.info(f"✅ Round {round_number} completed for session {session_id}")


    def save_player_answer(
        self,
        session_id: int,
        round_number: int,
        user_id: int,
        answer_data: dict
    ) -> bool:
        """
        Сохранить ответ игрока на вопрос.
        """
        answers_key = self._get_answers_key(session_id, round_number)
        logger.info(f"[SAVE_ANSWER] Key: {answers_key}, User: {user_id}")

        # Проверяем, не ответил ли уже
        if self.is_player_answered(session_id, round_number, user_id):
            logger.warning(f"Player {user_id} already answered round {round_number}")
            return False

        # Получаем текущие ответы
        answers = cache.get(answers_key, {})
        logger.info(f"[SAVE_ANSWER] Existing answers: {len(answers) if isinstance(answers, dict) else 0}")

        if not isinstance(answers, dict):
            answers = {}

        # Добавляем новый ответ
        answers[str(user_id)] = answer_data
        cache.set(answers_key, answers, timeout=self.TTL)

        # Проверяем, что сохранилось
        verify = cache.get(answers_key, {})
        logger.info(f"Saved answer for player {user_id} in round {round_number}. Total answers now: {len(verify) if isinstance(verify, dict) else 0}")
        logger.info(f"[SAVE_ANSWER] Verification - key exists: {str(user_id) in verify if isinstance(verify, dict) else False}")

        return True

    def get_round_answers(self, session_id: int, round_number: int) -> Dict[str, dict]:
        """
        Получить все ответы игроков на раунд.
        """
        answers_key = self._get_answers_key(session_id, round_number)
        answers = cache.get(answers_key, {})

        logger.info(f"[GET_ANSWERS] Key: {answers_key}, Type: {type(answers)}, Count: {len(answers) if isinstance(answers, dict) else 0}")

        if not isinstance(answers, dict):
            logger.warning(f"[GET_ANSWERS] Invalid type! Expected dict, got {type(answers)}")
            return {}

        return answers

    def is_player_answered(self, session_id: int, round_number: int, user_id: int) -> bool:
        """Проверить, ответил ли игрок на вопрос."""
        answers = self.get_round_answers(session_id, round_number)
        return str(user_id) in answers

    def get_round_answers_count(self, session_id: int, round_number: int) -> int:
        """Получить количество ответов на раунд."""
        answers = self.get_round_answers(session_id, round_number)
        count = len(answers)
        answers_key = self._get_answers_key(session_id, round_number)
        logger.info(f"[COUNT_ANSWERS] Key: {answers_key}, Count: {count}, Data: {list(answers.keys()) if answers else 'empty'}")
        return count


    def initialize_player_scores(self, session_id: int, user_ids: List[int]) -> None:
        """Инициализировать очки для всех игроков (0 баллов)."""
        scores_key = self._get_scores_key(session_id)
        scores = {str(user_id): 0 for user_id in user_ids}
        cache.set(scores_key, scores, timeout=self.TTL)
        logger.info(f"Initialized scores for {len(user_ids)} players in session {session_id}")

    def update_player_score(self, session_id: int, user_id: int, points_delta: int) -> int:
        """
        Обновить очки игрока (добавить points_delta).
        """
        scores_key = self._get_scores_key(session_id)
        scores = cache.get(scores_key, {})

        if not isinstance(scores, dict):
            scores = {}

        current_score = scores.get(str(user_id), 0)
        new_score = max(0, current_score + points_delta)
        scores[str(user_id)] = new_score

        cache.set(scores_key, scores, timeout=self.TTL)
        logger.info(f"Updated score for player {user_id}: {current_score} → {new_score} (+{points_delta})")

        return new_score

    def get_player_score(self, session_id: int, user_id: int) -> int:
        """Получить текущие очки игрока."""
        scores_key = self._get_scores_key(session_id)
        scores = cache.get(scores_key, {})

        if not isinstance(scores, dict):
            return 0

        return scores.get(str(user_id), 0)

    def get_player_scores(self, session_id: int) -> Dict[str, int]:
        """Получить очки всех игроков."""
        scores_key = self._get_scores_key(session_id)
        scores = cache.get(scores_key, {})

        if not isinstance(scores, dict):
            return {}

        return scores

    def get_leaderboard(self, session_id: int) -> List[dict]:
        """
        Получить таблицу лидеров (отсортированную по очкам).
        """
        scores = self.get_player_scores(session_id)

        # Сортируем по очкам (по убыванию)
        sorted_scores = sorted(
            [{'user_id': int(uid), 'score': score} for uid, score in scores.items()],
            key=lambda x: x['score'],
            reverse=True
        )

        # Добавляем ранги
        for rank, item in enumerate(sorted_scores, start=1):
            item['rank'] = rank

        return sorted_scores

    def _update_progress(self, session_id: int, current_round: int) -> None:
        """Обновить прогресс игры (внутренний метод)."""
        progress_key = self._get_progress_key(session_id)
        state = self.get_game_state(session_id)

        if not state:
            return

        total_questions = state.get('total_questions', 0)
        progress = {
            'current': current_round,
            'total': total_questions,
            'percent': round((current_round / total_questions * 100), 1) if total_questions > 0 else 0
        }

        cache.set(progress_key, json.dumps(progress), timeout=self.TTL)

    def get_game_progress(self, session_id: int) -> dict:
        """
        Получить прогресс игры.
        """
        progress_key = self._get_progress_key(session_id)
        progress_json = cache.get(progress_key)

        if not progress_json:
            # Попробовать восстановить из state
            state = self.get_game_state(session_id)
            if state:
                current_round = self.get_current_round(session_id)
                current = current_round.get('round_number', 0) if current_round else 0
                total = state.get('total_questions', 0)
                return {
                    'current': current,
                    'total': total,
                    'percent': round((current / total * 100), 1) if total > 0 else 0
                }
            return {'current': 0, 'total': 0, 'percent': 0}

        try:
            return json.loads(progress_json)
        except json.JSONDecodeError:
            return {'current': 0, 'total': 0, 'percent': 0}

    def get_round_statistics(self, session_id: int, round_number: int) -> dict:
        """
        Получить статистику раунда.
        """
        answers = self.get_round_answers(session_id, round_number)

        if not answers:
            return {
                'total_answers': 0,
                'correct_answers': 0,
                'average_time': 0,
                'fastest_time': 0
            }

        times = []
        correct_count = 0

        for answer_data in answers.values():
            if answer_data.get('is_correct'):
                correct_count += 1
            time_taken = answer_data.get('time_taken', 0)
            if time_taken > 0:
                times.append(time_taken)

        return {
            'total_answers': len(answers),
            'correct_answers': correct_count,
            'average_time': round(sum(times) / len(times), 2) if times else 0,
            'fastest_time': min(times) if times else 0
        }

    def clear_session(self, session_id: int) -> None:
        """Очистить всё состояние игровой сессии."""
        # Очистить основное состояние
        cache.delete(self._get_state_key(session_id))
        cache.delete(self._get_current_key(session_id))
        cache.delete(self._get_scores_key(session_id))
        cache.delete(self._get_progress_key(session_id))

        # Очистить раунды (до 1000 вопросов)
        for round_num in range(1, self.MAX_QUESTIONS + 1):
            round_key = self._get_round_key(session_id, round_num)
            if not cache.get(round_key):
                break
            cache.delete(round_key)
            cache.delete(self._get_answers_key(session_id, round_num))

        logger.info(f"🗑️ Cleared all data for session {session_id}")

    def refresh_session_ttl(self, session_id: int) -> None:
        """Обновить TTL сессии (продлить время жизни при активности)."""
        state = self.get_game_state(session_id)
        if state:
            self.save_game_state(session_id, state)

    def get_full_session_data(self, session_id: int) -> dict:
        """
        Получить полные данные сессии для отладки.
        """
        return {
            'state': self.get_game_state(session_id),
            'current_round': self.get_current_round(session_id),
            'scores': self.get_player_scores(session_id),
            'progress': self.get_game_progress(session_id)
        }

game_state_repository = RedisGameStateRepository()

