from typing import Optional, List, Dict
from apps.game.domain.events.game_events import (
    GameStarted,
    QuestionRevealed,
    PlayerAnswerSubmitted,
    AnswerChecked,
    RoundCompleted,
    GameFinished,
    GamePaused,
    GameResumed
)


class GameSessionDomainService:
    """
    Доменный сервис для управления игровой сессией.
    """

    def __init__(self, game_state_repo):
        """
        game_state_repo: IGameStateRepository
        """
        self.game_state_repo = game_state_repo

    def start_game(
        self,
        session_id: int,
        room_id: int,
        quiz_id: int,
        quiz_title: str,
        total_questions: int,
        started_by: int
    ) -> GameStarted:
        """
        Начать игру.
        """
        from django.utils import timezone

        state_data = {
            'session_id': session_id,
            'room_id': room_id,
            'quiz_id': quiz_id,
            'quiz_title': quiz_title,
            'status': 'playing',
            'total_questions': total_questions,
            'started_at': timezone.now().isoformat(),
            'started_by': started_by
        }

        self.game_state_repo.save_game_state(session_id, state_data)

        event = GameStarted(
            room_id=room_id,
            session_id=session_id,
            quiz_id=quiz_id,
            quiz_title=quiz_title,
            total_questions=total_questions,
            started_by=started_by
        )

        return event

    def reveal_question(
        self,
        session_id: int,
        room_id: int,
        round_number: int,
        question_id: int,
        question_text: str,
        options: List[Dict],
        time_limit: int,
        points: int,
        difficulty: str = "medium"
    ) -> QuestionRevealed:
        """
        Показать новый вопрос игрокам.
        """
        from django.utils import timezone

        question_data = {
            'round_number': round_number,
            'question_id': question_id,
            'question_text': question_text,
            'options': options,
            'time_limit': time_limit,
            'points': points,
            'difficulty': difficulty,
            'started_at': timezone.now().isoformat(),
            'status': 'active'
        }

        self.game_state_repo.set_current_round(session_id, round_number, question_data)

        event = QuestionRevealed(
            room_id=room_id,
            session_id=session_id,
            round_number=round_number,
            question_id=question_id,
            question_text=question_text,
            options=options,
            time_limit=time_limit,
            points=points,
            difficulty=difficulty
        )

        return event

    def submit_answer(
        self,
        session_id: int,
        room_id: int,
        round_number: int,
        user_id: int,
        username: str,
        answer_option_id: int,
        time_taken: float
    ) -> Optional[PlayerAnswerSubmitted]:
        """
        Принять ответ игрока.
        """
        from django.utils import timezone

        # Проверяем, не ответил ли уже
        if self.game_state_repo.is_player_answered(session_id, round_number, user_id):
            return None

        # Определяем, первый ли ответ
        current_answers_count = self.game_state_repo.get_round_answers_count(session_id, round_number)
        is_first = current_answers_count == 0

        answer_data = {
            'user_id': user_id,
            'username': username,
            'answer_option_id': answer_option_id,
            'time_taken': time_taken,
            'answered_at': timezone.now().isoformat(),
            'is_first': is_first,
            'is_correct': None
        }

        # Сохраняем в Redis
        success = self.game_state_repo.save_player_answer(
            session_id, round_number, user_id, answer_data
        )

        if not success:
            return None

        event = PlayerAnswerSubmitted(
            room_id=room_id,
            session_id=session_id,
            round_number=round_number,
            user_id=user_id,
            username=username,
            answer_option_id=answer_option_id,
            time_taken=time_taken,
            is_first=is_first
        )

        return event

    def check_answer(
        self,
        session_id: int,
        room_id: int,
        round_number: int,
        user_id: int,
        username: str,
        is_correct: bool,
        points_earned: int
    ) -> AnswerChecked:
        """
        Проверить ответ и начислить очки.
        """
        # Обновляем очки в Redis
        new_score = self.game_state_repo.update_player_score(session_id, user_id, points_earned)

        # Обновляем ответ в Redis
        answers = self.game_state_repo.get_round_answers(session_id, round_number)
        if str(user_id) in answers:
            answers[str(user_id)]['is_correct'] = is_correct
            answers[str(user_id)]['points_earned'] = points_earned
            # Пересохраняем
            answers_key = self.game_state_repo._get_answers_key(session_id, round_number)
            from django.core.cache import cache
            cache.set(answers_key, answers, timeout=self.game_state_repo.TTL)

        event = AnswerChecked(
            room_id=room_id,
            session_id=session_id,
            round_number=round_number,
            user_id=user_id,
            username=username,
            is_correct=is_correct,
            points_earned=points_earned,
            time_taken=0.0,  # TODO: взять из ответа
            current_score=new_score
        )

        return event

    def complete_round(
        self,
        session_id: int,
        room_id: int,
        round_number: int,
        question_id: int,
        correct_option_id: int,
        explanation: str = ""
    ) -> RoundCompleted:
        """
        Завершить раунд и собрать результаты.
        """
        # Получаем все ответы
        answers = self.game_state_repo.get_round_answers(session_id, round_number)

        # Формируем результаты
        results = []
        for user_id_str, answer_data in answers.items():
            results.append({
                'user_id': answer_data.get('user_id'),
                'username': answer_data.get('username'),
                'is_correct': answer_data.get('is_correct', False),
                'points': answer_data.get('points_earned', 0),
                'time': answer_data.get('time_taken', 0.0)
            })

        # Сортируем по времени ответа (кто быстрее)
        results.sort(key=lambda x: x['time'])

        # Получаем статистику
        statistics = self.game_state_repo.get_round_statistics(session_id, round_number)

        # Помечаем раунд как завершенный
        self.game_state_repo.complete_round(session_id, round_number)

        event = RoundCompleted(
            room_id=room_id,
            session_id=session_id,
            round_number=round_number,
            question_id=question_id,
            correct_option_id=correct_option_id,
            explanation=explanation,
            results=results,
            statistics=statistics
        )

        return event

    def finish_game(
        self,
        session_id: int,
        room_id: int,
        quiz_title: str,
        total_rounds: int
    ) -> GameFinished:
        """
        Завершить игру и показать итоги.
        """
        # Получаем таблицу лидеров
        leaderboard = self.game_state_repo.get_leaderboard(session_id)

        # Получаем имена игроков из ответов (берем из первого раунда)
        answers_round_1 = self.game_state_repo.get_round_answers(session_id, 1)
        username_map = {
            int(uid): data.get('username', f'Игрок {uid}')
            for uid, data in answers_round_1.items()
        }

        # Формируем финальные результаты
        final_results = []
        for item in leaderboard:
            user_id = item['user_id']
            final_results.append({
                'user_id': user_id,
                'username': username_map.get(user_id, f'Игрок {user_id}'),
                'total_points': item['score'],
                'rank': item['rank']
            })

        # Определяем победителя
        winner = final_results[0] if final_results else None
        winner_id = winner['user_id'] if winner else None
        winner_username = winner['username'] if winner else None

        # Обновляем статус сессии
        self.game_state_repo.update_session_status(session_id, 'finished')

        event = GameFinished(
            room_id=room_id,
            session_id=session_id,
            quiz_title=quiz_title,
            total_rounds=total_rounds,
            final_results=final_results,
            winner_id=winner_id,
            winner_username=winner_username
        )

        return event

    def pause_game(self, session_id: int, room_id: int, paused_by: int) -> GamePaused:
        """Поставить игру на паузу."""
        current_round = self.game_state_repo.get_current_round(session_id)
        current_round_num = current_round.get('round_number', 0) if current_round else 0

        self.game_state_repo.update_session_status(session_id, 'paused')

        event = GamePaused(
            room_id=room_id,
            session_id=session_id,
            paused_by=paused_by,
            current_round=current_round_num
        )

        return event

    def resume_game(self, session_id: int, room_id: int, resumed_by: int) -> GameResumed:
        """Продолжить игру после паузы."""
        current_round = self.game_state_repo.get_current_round(session_id)
        current_round_num = current_round.get('round_number', 0) if current_round else 0

        self.game_state_repo.update_session_status(session_id, 'playing')

        event = GameResumed(
            room_id=room_id,
            session_id=session_id,
            resumed_by=resumed_by,
            current_round=current_round_num
        )

        return event

    def get_current_state(self, session_id: int) -> dict:
        """
        Получить текущее состояние игры.
        """
        state = self.game_state_repo.get_game_state(session_id)
        current_round = self.game_state_repo.get_current_round(session_id)
        progress = self.game_state_repo.get_game_progress(session_id)
        scores = self.game_state_repo.get_player_scores(session_id)

        return {
            'status': state.get('status') if state else 'unknown',
            'current_round': current_round,
            'progress': progress,
            'scores': scores
        }

