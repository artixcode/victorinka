from typing import Optional, Dict, List
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from apps.game.infrastructure.redis_game_state_repository import game_state_repository
from apps.game.domain.services.game_session_service import GameSessionDomainService
from apps.game.domain.services.round_timer_service import RoundTimerService
from apps.questions.models import Quiz, AnswerOption
from apps.rooms.models import Room
from apps.game.models import GameSession, GameRound, PlayerAnswer, PlayerGameStats
from apps.game.tasks import start_round_timer

logger = logging.getLogger(__name__)


class GameCoordinatorService:
    """
    Application Service для координации игрового процесса.
    """

    def __init__(self):
        self.game_state_repo = game_state_repository
        self.domain_service = GameSessionDomainService(game_state_repository)
        self.timer_service = RoundTimerService(game_state_repository)

    def start_game_session(self, session_id: int, user_id: int) -> dict:
        """
        Начать игровую сессию через WebSocket.
        """
        session = get_object_or_404(GameSession, id=session_id)

        # Проверка прав
        if session.room.host_id != user_id:
            raise PermissionError("Только хост может начать игру")

        # Проверка статуса
        if session.status != GameSession.Status.WAITING:
            raise ValueError(f"Невозможно начать игру в статусе: {session.get_status_display()}")

        # Обновляем PostgreSQL
        session.start()

        # Получаем данные викторины
        quiz = session.quiz
        total_questions = quiz.questions.count()

        # Получаем список игроков
        participant_ids = list(
            session.room.participants.values_list('user_id', flat=True)
        )

        # Инициализируем очки в Redis
        self.game_state_repo.initialize_player_scores(session_id, participant_ids)

        # Генерируем событие через domain service
        game_started_event = self.domain_service.start_game(
            session_id=session.id,
            room_id=session.room_id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            total_questions=total_questions,
            started_by=user_id
        )

        # Получаем и показываем первый вопрос
        first_question_data = self.get_next_question(session_id)

        return {
            'game_started_event': game_started_event,
            'first_question_event': first_question_data.get('question_revealed_event') if first_question_data else None
        }

    def get_next_question(self, session_id: int) -> Optional[dict]:
        """
        Получить следующий вопрос и показать его игрокам.
        """
        session = get_object_or_404(GameSession, id=session_id)

        # Получаем следующий раунд
        next_round_number = session.current_question_index + 1
        next_round = session.rounds.filter(round_number=next_round_number).first()

        if not next_round:
            # Вопросов больше нет
            return None

        # Запускаем раунд в PostgreSQL
        if next_round.status == GameRound.Status.WAITING:
            next_round.start()

        session.current_question_index = next_round_number
        session.save(update_fields=['current_question_index'])
        logger.info(f"Set current round {next_round_number} for session {session_id}")

        # Получаем данные вопроса
        question = next_round.question
        options = list(question.options.values('id', 'text', 'order'))

        # Генерируем событие через domain service
        question_revealed_event = self.domain_service.reveal_question(
            session_id=session.id,
            room_id=session.room_id,
            round_number=next_round_number,
            question_id=question.id,
            question_text=question.text,
            options=options,
            time_limit=next_round.time_limit,
            points=question.points,
            difficulty=question.difficulty
        )

        timer_duration = self.timer_service.calculate_round_duration(
            question_difficulty=question.difficulty,
            custom_duration=next_round.time_limit
        )

        start_round_timer.delay(
            session_id=session.id,
            room_id=session.room_id,
            round_number=next_round_number,
            duration_seconds=timer_duration
        )

        self.timer_service.start_timer(
            session_id=session.id,
            round_number=next_round_number,
            duration_seconds=timer_duration
        )

        logger.info(f"Запущен таймер для раунда {next_round_number}, длительность: {timer_duration}с")

        return {
            'question_revealed_event': question_revealed_event,
            'round_id': next_round.id,
            'round_number': next_round_number,
            'question_id': question.id,
            'question_text': question.text,
            'options': options,
            'total_questions': session.quiz.questions.count(),
            'timer_duration': timer_duration
        }

    def submit_answer(self, session_id: int, user_id: int, username: str, answer_option_id: int, time_taken: int = 0) -> dict:
        """
        Отправить ответ игрока.
        """
        from apps.game.models import GameSession

        session = get_object_or_404(GameSession, id=session_id)
        current_round_number = session.current_question_index

        if current_round_number == 0:
            raise ValueError("Активный раунд не найден")

        current_round = session.rounds.filter(round_number=current_round_number).first()
        if not current_round:
            raise ValueError("Активный раунд не найден")

        answer_submitted_event = self.domain_service.submit_answer(
            session_id=session.id,
            room_id=session.room_id,
            round_number=current_round_number,
            user_id=user_id,
            username=username,
            answer_option_id=answer_option_id,
            time_taken=time_taken
        )

        if not answer_submitted_event:
            raise ValueError("Вы уже ответили на этот вопрос")

        # Проверяем правильность ответа
        answer_option = get_object_or_404(AnswerOption, id=answer_option_id)
        is_correct = answer_option.is_correct
        points_earned = current_round.question.points if is_correct else 0

        # Начисляем очки
        answer_checked_event = self.domain_service.check_answer(
            session_id=session.id,
            room_id=session.room_id,
            round_number=current_round_number,
            user_id=user_id,
            username=username,
            is_correct=is_correct,
            points_earned=points_earned
        )

        total_participants = session.room.participants.count()
        total_answers = self.game_state_repo.get_round_answers_count(session_id, current_round_number)
        should_complete_round = False

        if total_answers >= total_participants:
            # Все игроки ответили - завершаем раунд
            should_complete_round = True
            logger.info(f"[SUBMIT_ANSWER] Все игроки ответили ({total_answers}/{total_participants})")
        elif is_correct and total_answers == 1:
            # Первый игрок ответил правильно - завершаем раунд
            should_complete_round = True
            logger.info(f"[SUBMIT_ANSWER] Первый игрок ответил правильно - завершаем раунд")
        else:
            should_complete_round = False
            logger.info(f"[SUBMIT_ANSWER] Ждем ответов ({total_answers}/{total_participants})")

        logger.info(f"[SUBMIT_ANSWER] Раунд {current_round_number}: ответов {total_answers}/{total_participants}, завершаем={should_complete_round}")

        result = {
            'answer_submitted_event': answer_submitted_event,
            'answer_checked_event': answer_checked_event,
            'should_complete_round': should_complete_round
        }

        return result

    def complete_current_round(self, session_id: int) -> dict:
        """
        Завершить текущий раунд.
        """
        logger.info(f"[COMPLETE_ROUND] Starting for session {session_id}")
        session = get_object_or_404(GameSession, id=session_id)
        current_round_number = session.current_question_index
        logger.info(f"[COMPLETE_ROUND] Current round number: {current_round_number}")

        current_round = session.rounds.filter(round_number=current_round_number).first()

        if not current_round:
            logger.error(f"[COMPLETE_ROUND] Round {current_round_number} not found!")
            raise ValueError("Текущий раунд не найден")

        logger.info(f"[COMPLETE_ROUND] Round found: {current_round.id}, status: {current_round.status}")

        correct_option = current_round.question.options.filter(is_correct=True).first()
        if not correct_option:
            raise ValueError("Правильный ответ не найден для вопроса")

        self._sync_round_to_database(session, current_round)

        current_round.complete()
        logger.info(f"[COMPLETE_ROUND] Round {current_round_number} completed in DB")

        round_completed_event = self.domain_service.complete_round(
            session_id=session.id,
            room_id=session.room_id,
            round_number=current_round_number,
            question_id=current_round.question_id,
            correct_option_id=correct_option.id,
            explanation=current_round.question.explanation
        )

        # Проверяем, есть ли следующий вопрос
        total_questions = session.quiz.questions.count()
        has_next = current_round_number < total_questions

        logger.info(f"[COMPLETE_ROUND] has_next={has_next} (current={current_round_number}, total={total_questions})")

        if has_next:
            next_question_data = self.get_next_question(session_id)
            logger.info(f"[COMPLETE_ROUND] Got next question data")
        else:
            # Игра завершена
            logger.info(f"[COMPLETE_ROUND] No more questions, finishing game...")
            next_question_data = None
            self._finish_game_session(session)

        return {
            'round_completed_event': round_completed_event,
            'has_next': has_next,
            'next_question_data': next_question_data
        }

    def _sync_round_to_database(self, session, current_round) -> None:
        """
        Синхронизировать ответы из Redis в PostgreSQL.
        """
        answers = self.game_state_repo.get_round_answers(session.id, current_round.round_number)

        # Создаем PlayerAnswer записи
        for user_id_str, answer_data in answers.items():
            user_id = int(user_id_str)

            # Проверяем, не создан ли уже
            if PlayerAnswer.objects.filter(round=current_round, user_id=user_id).exists():
                continue

            answer_option_id = answer_data.get('answer_option_id')
            is_correct = answer_data.get('is_correct', False)
            points_earned = answer_data.get('points_earned', 0)
            time_taken = answer_data.get('time_taken', 0.0)

            PlayerAnswer.objects.create(
                round=current_round,
                user_id=user_id,
                selected_option_id=answer_option_id,
                is_correct=is_correct,
                points_earned=points_earned,
                time_taken=time_taken
            )

            stats = PlayerGameStats.objects.filter(session=session, user_id=user_id).first()
            if stats:
                stats.total_points += points_earned
                if is_correct:
                    stats.correct_answers += 1
                stats.save(update_fields=['total_points', 'correct_answers'])

        logger.info(f"Synced {len(answers)} answers to PostgreSQL for round {current_round.round_number}")

    def _finish_game_session(self, session) -> dict:
        """
        Завершить игровую сессию.
        """
        session.finish()

        session.room.status = Room.Status.FINISHED
        session.room.save(update_fields=['status'])

        for stats in session.player_stats.all():
            stats.finalize()

        ranked_stats = session.player_stats.order_by('-total_points', 'completed_at')
        for rank, stats in enumerate(ranked_stats, start=1):
            stats.rank = rank
            stats.save(update_fields=['rank'])

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

        for stats in session.player_stats.all():
            stats.user.total_points += stats.total_points
            stats.user.save(update_fields=['total_points'])
            logger.info(f"Updated total_points for {stats.user.nickname}: +{stats.total_points}")

        winner = session.player_stats.filter(rank=1).first()
        if winner:
            winner.user.total_wins += 1
            winner.user.save(update_fields=['total_wins'])
            logger.info(f"Winner {winner.user.nickname} total_wins: {winner.user.total_wins}")

        game_finished_event = self.domain_service.finish_game(
            session_id=session.id,
            room_id=session.room_id,
            quiz_title=session.quiz.title,
            total_rounds=total_questions
        )

        logger.info(f"Game session {session.id} finished")

        return {
            'game_finished_event': game_finished_event
        }

    def pause_game_session(self, session_id: int, user_id: int) -> dict:
        """Поставить игру на паузу через WebSocket."""
        session = get_object_or_404(GameSession, id=session_id)

        if session.room.host_id != user_id:
            raise PermissionError("Только хост может поставить игру на паузу")

        if session.status != GameSession.Status.PLAYING:
            raise ValueError("Невозможно поставить на паузу игру в текущем статусе")

        session.pause()

        pause_event = self.domain_service.pause_game(
            session_id=session.id,
            room_id=session.room_id,
            paused_by=user_id
        )

        return {
            'game_paused_event': pause_event
        }

    def resume_game_session(self, session_id: int, user_id: int) -> dict:
        """Продолжить игру после паузы через WebSocket."""
        from apps.game.models import GameSession

        session = get_object_or_404(GameSession, id=session_id)

        if session.room.host_id != user_id:
            raise PermissionError("Только хост может продолжить игру")

        if session.status != GameSession.Status.PAUSED:
            raise ValueError("Невозможно продолжить игру в текущем статусе")

        session.resume()

        resume_event = self.domain_service.resume_game(
            session_id=session.id,
            room_id=session.room_id,
            resumed_by=user_id
        )

        return {
            'game_resumed_event': resume_event
        }

    def get_current_game_state(self, session_id: int) -> dict:
        """
        Получить текущее состояние игры для отправки игроку.
        """
        state = self.game_state_repo.get_game_state(session_id)
        current_question = self.game_state_repo.get_current_round(session_id)
        progress = self.game_state_repo.get_game_progress(session_id)
        scores = self.game_state_repo.get_player_scores(session_id)

        return {
            'session_id': session_id,
            'status': state.get('status') if state else 'unknown',
            'quiz_title': state.get('quiz_title') if state else '',
            'current_question': current_question,
            'progress': progress,
            'scores': scores
        }

    def sync_to_database(self, session_id: int) -> None:
        """
        Полная синхронизация состояния из Redis в PostgreSQL.
        """
        session = get_object_or_404(GameSession, id=session_id)

        # Синхронизируем все завершенные раунды
        for round_obj in session.rounds.filter(status=GameRound.Status.COMPLETED):
            self._sync_round_to_database(session, round_obj)

        logger.info(f"Full sync to database completed for session {session_id}")

    def auto_complete_round(self, session_id: int, round_number: int, reason: str = 'time_expired') -> dict:
        """
        Автоматически завершить раунд
        """
        from apps.game.models import GameSession

        logger.info(f"Автозавершение раунда {round_number} для сессии {session_id}, причина: {reason}")

        try:
            session = get_object_or_404(GameSession, id=session_id)

            session.current_question_index = round_number
            session.save(update_fields=['current_question_index'])
            logger.info(f"Set current round {round_number} for session {session_id}")

            self.timer_service.stop_timer(session_id, round_number, reason=reason)
            logger.info(f"Таймер остановлен для раунда {round_number}, причина: {reason}")

            result = self.complete_current_round(session_id)

            logger.info(f"Таймер раунда {round_number} завершен успешно")
            return result

        except Exception as e:
            logger.error(f"Ошибка в таймере раунда {round_number}: {e}", exc_info=True)
            raise

game_coordinator_service = GameCoordinatorService()

