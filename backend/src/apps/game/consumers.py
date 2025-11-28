import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from apps.game.models import GameSession


class GameRoomConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для игровой комнаты.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = None
        self.room_group_name = None
        self.user = None
        self.user_id = None
        self.username = None

    async def connect(self):
        """
        Принятие WebSocket соединения.
        """
        # Получаем room_id из URL
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_room_{self.room_id}'

        # Получаем пользователя из scope
        self.user = self.scope.get('user')

        # Проверяем аутентификацию
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_id = self.user.id
        self.username = self.user.nickname or self.user.email

        # Проверяем существование комнаты
        room_exists = await self._check_room_exists(self.room_id)
        if not room_exists:
            await self.close(code=4004)
            return

        # Принимаем соединение
        await self.accept()

        # Инициализируем метаданные комнаты в Redis (если еще нет)
        await self._initialize_room_metadata()

        # Добавляем в группу
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Обрабатываем присоединение
        join_data = await self.handle_join()

        # Уведомляем всех в комнате
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player_joined',
                'data': join_data
            }
        )

        # Отправляем текущее состояние комнаты только этому клиенту
        room_state = await self.get_room_state()
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'data': room_state
        }))

    async def disconnect(self, close_code):
        """
        Отключение от WebSocket.
        """
        if self.room_group_name and self.user_id:
            # Обрабатываем выход
            leave_data = await self.handle_leave()

            # Уведомляем всех в комнате
            if leave_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'player_left',
                        'data': leave_data
                    }
                )

            # Удаляем из группы
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """
        Получение сообщения от клиента.
        """
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'get_state':
                await self.send_room_state()
            elif message_type == 'start_game':
                await self.handle_start_game(data)
            elif message_type == 'submit_answer':
                await self.handle_submit_answer(data)
            elif message_type == 'next_question':
                await self.handle_next_question(data)
            elif message_type == 'pause_game':
                await self.handle_pause_game(data)
            elif message_type == 'resume_game':
                await self.handle_resume_game(data)
            elif message_type == 'get_game_state':
                await self.send_game_state()
            else:
                await self.send_error(f'Неизвестный тип сообщения: {message_type}')

        except json.JSONDecodeError:
            await self.send_error('Неверный формат JSON')
        except Exception as e:
            await self.send_error(f'Ошибка обработки: {str(e)}')

    async def handle_join(self):
        """Обработка присоединения игрока."""
        from apps.game.application.services.websocket_room_service import websocket_room_service

        return await sync_to_async(websocket_room_service.handle_player_join)(
            room_id=int(self.room_id),
            user_id=self.user_id,
            username=self.username,
            channel_name=self.channel_name
        )

    async def handle_leave(self):
        """Обработка выхода игрока."""
        from apps.game.application.services.websocket_room_service import websocket_room_service

        return await sync_to_async(websocket_room_service.handle_player_leave)(
            room_id=int(self.room_id),
            user_id=self.user_id,
            username=self.username,
            channel_name=self.channel_name
        )

    async def handle_chat_message(self, data):
        """Обработка сообщения в чате."""
        from apps.game.application.services.websocket_room_service import websocket_room_service

        message = data.get('message', '').strip()
        if not message:
            await self.send_error('Сообщение не может быть пустым')
            return

        result = await sync_to_async(websocket_room_service.handle_chat_message)(
            room_id=int(self.room_id),
            user_id=self.user_id,
            username=self.username,
            message=message
        )

        if not result:
            await self.send_error('Не удалось отправить сообщение')
            return

        # Проверяем на ошибку валидации
        if result.get('error'):
            await self.send_error(result.get('message', 'Ошибка валидации'))
            return

        # Рассылаем сообщение всем в комнате
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data': result
            }
        )

    async def get_room_state(self):
        """Получить состояние комнаты."""
        from apps.game.application.services.websocket_room_service import websocket_room_service

        return await sync_to_async(websocket_room_service.get_room_state)(
            room_id=int(self.room_id)
        )

    async def send_room_state(self):
        """Отправить состояние комнаты клиенту."""
        room_state = await self.get_room_state()
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'data': room_state
        }))

    async def player_joined(self, event):
        """Событие: игрок присоединился."""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'data': event['data']
        }))

    async def player_left(self, event):
        """Событие: игрок вышел."""
        await self.send(text_data=json.dumps({
            'type': 'player_left',
            'data': event['data']
        }))

    async def chat_message(self, event):
        """Событие: сообщение в чате."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['data']
        }))


    async def handle_start_game(self, data):
        """Обработка начала игры (только хост)."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service
        from apps.rooms.models import Room
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"🎮 [START_GAME] User {self.user_id} ({self.username}) trying to start game in room {self.room_id}")

        try:
            # Проверяем, что пользователь - хост комнаты
            room = await database_sync_to_async(Room.objects.get)(id=self.room_id)
            logger.info(f"🎮 [START_GAME] Room found. Host: {room.host_id}, Current user: {self.user_id}")

            if room.host_id != self.user_id:
                logger.warning(f"[START_GAME] Permission denied: user {self.user_id} is not host")
                await self.send_error('Только хост может начать игру')
                return

            # Получаем активную сессию
            session = await database_sync_to_async(
                lambda: room.game_sessions.filter(
                    status=GameSession.Status.WAITING
                ).first()
            )()

            if not session:
                logger.error(f"🎮 [START_GAME] No waiting session found in room {self.room_id}")
                await self.send_error('Нет активной игровой сессии. Создайте сессию через API: POST /api/game/rooms/{room_id}/start/ с {"quiz_id": X}')
                return

            logger.info(f"[START_GAME] Session {session.id} found, starting game...")

            # Запускаем игру через coordinator
            result = await sync_to_async(game_coordinator_service.start_game_session)(
                session_id=session.id,
                user_id=self.user_id
            )

            logger.info(f"[START_GAME] Game started successfully. Broadcasting events...")

            # Broadcast события
            if result.get('game_started_event'):
                await self._broadcast_game_event('game_started', result['game_started_event'])
                logger.info(f"[START_GAME] Broadcasted game_started event")

            if result.get('first_question_event'):
                await self._broadcast_game_event('question_revealed', result['first_question_event'])
                logger.info(f"[START_GAME] Broadcasted question_revealed event")

        except Room.DoesNotExist:
            logger.error(f"🎮 [START_GAME] Room {self.room_id} not found")
            await self.send_error(f'Комната {self.room_id} не найдена')
        except PermissionError as e:
            logger.error(f"🎮 [START_GAME] Permission error: {str(e)}")
            await self.send_error(str(e))
        except ValueError as e:
            logger.error(f"🎮 [START_GAME] Value error: {str(e)}")
            await self.send_error(str(e))
        except Exception as e:
            logger.exception(f"🎮 [START_GAME] Unexpected error: {str(e)}")
            await self.send_error(f'Ошибка запуска игры: {str(e)}')

    async def handle_submit_answer(self, data):
        """Обработка отправки ответа игроком."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"[SUBMIT_ANSWER] Player {self.user_id} submitting answer...")

        try:
            answer_option_id = data.get('answer_option_id')
            time_taken = data.get('time_taken', 0.0)

            if not answer_option_id:
                await self.send_error('Не указан вариант ответа')
                return

            # Получаем активную сессию
            session = await self._get_active_session()
            if not session:
                await self.send_error('Активная игровая сессия не найдена')
                return

            # Отправляем ответ через coordinator
            result = await sync_to_async(game_coordinator_service.submit_player_answer)(
                session_id=session.id,
                user_id=self.user_id,
                username=self.username,
                answer_option_id=answer_option_id,
                time_taken=time_taken
            )

            # Broadcast события
            if result.get('answer_submitted_event'):
                await self._broadcast_game_event('answer_submitted', result['answer_submitted_event'])

            if result.get('answer_checked_event'):
                # Отправляем результат только игроку
                await self.send(text_data=json.dumps({
                    'type': 'answer_checked',
                    'data': self._event_to_dict(result['answer_checked_event'])
                }))

            # Если все ответили - завершаем раунд
            if result.get('should_complete_round'):
                logger.info(f"[SUBMIT_ANSWER] Все ответили! Завершаем раунд...")
                await self._complete_round(session.id)
            else:
                logger.info(f"[SUBMIT_ANSWER] Ожидаем ответов от других игроков...")

        except ValueError as e:
            await self.send_error(str(e))
        except Exception as e:
            await self.send_error(f'Ошибка отправки ответа: {str(e)}')

    async def handle_next_question(self, data):
        """Обработка запроса следующего вопроса (только хост или авто)."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service

        try:
            session = await self._get_active_session()
            if not session:
                await self.send_error('Активная игровая сессия не найдена')
                return

            # Получаем следующий вопрос
            result = await sync_to_async(game_coordinator_service.get_next_question)(
                session_id=session.id
            )

            if result and result.get('question_revealed_event'):
                await self._broadcast_game_event('question_revealed', result['question_revealed_event'])

        except Exception as e:
            await self.send_error(f'Ошибка получения следующего вопроса: {str(e)}')

    async def handle_pause_game(self, data):
        """Обработка паузы игры (только хост)."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service
        from apps.rooms.models import Room

        try:
            room = await database_sync_to_async(Room.objects.get)(id=self.room_id)
            if room.host_id != self.user_id:
                await self.send_error('Только хост может поставить игру на паузу')
                return

            session = await self._get_active_session()
            if not session:
                return

            result = await sync_to_async(game_coordinator_service.pause_game_session)(
                session_id=session.id,
                user_id=self.user_id
            )

            if result.get('game_paused_event'):
                await self._broadcast_game_event('game_paused', result['game_paused_event'])

        except PermissionError as e:
            await self.send_error(str(e))
        except Exception as e:
            await self.send_error(f'Ошибка паузы: {str(e)}')

    async def handle_resume_game(self, data):
        """Обработка продолжения игры (только хост)."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service
        from apps.rooms.models import Room

        try:
            room = await database_sync_to_async(Room.objects.get)(id=self.room_id)
            if room.host_id != self.user_id:
                await self.send_error('Только хост может продолжить игру')
                return

            session = await self._get_active_session()
            if not session:
                return

            result = await sync_to_async(game_coordinator_service.resume_game_session)(
                session_id=session.id,
                user_id=self.user_id
            )

            if result.get('game_resumed_event'):
                await self._broadcast_game_event('game_resumed', result['game_resumed_event'])

        except PermissionError as e:
            await self.send_error(str(e))
        except Exception as e:
            await self.send_error(f'Ошибка продолжения: {str(e)}')

    async def send_game_state(self):
        """Отправить текущее состояние игры клиенту."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service

        try:
            session = await self._get_active_session()
            if not session:
                await self.send_error('Активная игровая сессия не найдена')
                return

            game_state = await sync_to_async(game_coordinator_service.get_current_game_state)(
                session_id=session.id
            )

            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'data': game_state
            }))

        except Exception as e:
            await self.send_error(f'Ошибка получения состояния игры: {str(e)}')

    async def _complete_round(self, session_id: int):
        """Завершить текущий раунд (внутренний метод)."""
        from apps.game.application.services.game_coordinator_service import game_coordinator_service
        import asyncio
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"[COMPLETE_ROUND] Starting round completion for session {session_id}")

        try:
            # Завершаем раунд через coordinator
            result = await sync_to_async(game_coordinator_service.complete_current_round)(
                session_id=session_id
            )

            logger.info(f"[COMPLETE_ROUND] Coordinator returned: has_next={result.get('has_next')}")

            # Broadcast результаты раунда
            if result.get('round_completed_event'):
                await self._broadcast_game_event('round_completed', result['round_completed_event'])
                logger.info(f"[COMPLETE_ROUND] Broadcasted round_completed event")

            # Ждем 3 секунды перед следующим вопросом
            logger.info(f"[COMPLETE_ROUND] Waiting 3 seconds before next question...")
            await asyncio.sleep(3)

            # Показываем следующий вопрос или завершаем игру
            if result.get('has_next') and result.get('next_question_data'):
                next_event = result['next_question_data'].get('question_revealed_event')
                if next_event:
                    logger.info(f"[COMPLETE_ROUND] Broadcasting next question...")
                    await self._broadcast_game_event('question_revealed', next_event)
                    logger.info(f"[COMPLETE_ROUND] Next question broadcasted!")
                else:
                    logger.warning(f"[COMPLETE_ROUND] next_question_data exists but no event")
            else:
                logger.info(f"[COMPLETE_ROUND] No more questions, game should be finished")

        except Exception as e:
            logger.exception(f"[COMPLETE_ROUND] Error: {str(e)}")
            await self.send_error(f'Ошибка завершения раунда: {str(e)}')

    async def _broadcast_game_event(self, event_type: str, event_obj):
        """Broadcast игрового события всем в комнате."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': event_type,
                'data': self._event_to_dict(event_obj)
            }
        )

    def _event_to_dict(self, event_obj) -> dict:
        from dataclasses import asdict
        data = asdict(event_obj)

        if 'timestamp' in data and data['timestamp']:
            data['timestamp'] = data['timestamp'].isoformat()

        return data


    async def game_started(self, event):
        """Событие: игра началась."""
        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'data': event['data']
        }))

    async def question_revealed(self, event):
        """Событие: показан новый вопрос."""
        await self.send(text_data=json.dumps({
            'type': 'question_revealed',
            'data': event['data']
        }))

    async def new_question(self, event):
        """Событие: следующий вопрос (после автозавершения раунда)."""
        await self.send(text_data=json.dumps({
            'type': 'new_question',
            'session_id': event['session_id'],
            'round_number': event['round_number'],
            'question_id': event['question_id'],
            'question_text': event['question_text'],
            'options': event['options'],
            'total_questions': event['total_questions'],
            'timer_duration': event.get('timer_duration', 30)
        }))

    async def answer_submitted(self, event):
        """Событие: игрок отправил ответ."""
        await self.send(text_data=json.dumps({
            'type': 'answer_submitted',
            'data': event['data']
        }))

    async def answer_checked(self, event):
        """Событие: ответ проверен."""
        await self.send(text_data=json.dumps({
            'type': 'answer_checked',
            'data': event['data']
        }))

    async def round_completed(self, event):
        """Событие: раунд завершен."""
        await self.send(text_data=json.dumps({
            'type': 'round_completed',
            'data': event['data']
        }))

    async def game_finished(self, event):
        """Событие: игра завершена."""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'session_id': event.get('session_id'),
            'message': event.get('message', 'Игра завершена')
        }))

    async def game_paused(self, event):
        """Событие: игра на паузе."""
        await self.send(text_data=json.dumps({
            'type': 'game_paused',
            'data': event['data']
        }))

    async def game_resumed(self, event):
        """Событие: игра продолжена."""
        await self.send(text_data=json.dumps({
            'type': 'game_resumed',
            'data': event['data']
        }))

    async def timer_update(self, event):
        """Событие: обновление таймера раунда."""
        await self.send(text_data=json.dumps({
            'type': 'timer_update',
            'session_id': event['session_id'],
            'round_number': event['round_number'],
            'remaining_seconds': event['remaining_seconds'],
            'total_seconds': event['total_seconds']
        }))

    async def timer_paused(self, event):
        """Событие: таймер остановлен на паузу."""
        await self.send(text_data=json.dumps({
            'type': 'timer_paused',
            'session_id': event['session_id'],
            'round_number': event['round_number'],
            'paused_at_seconds': event['paused_at_seconds']
        }))

    async def timer_resumed(self, event):
        """Событие: таймер возобновлен после паузы."""
        await self.send(text_data=json.dumps({
            'type': 'timer_resumed',
            'session_id': event['session_id'],
            'round_number': event['round_number'],
            'remaining_seconds': event['remaining_seconds'],
            'pause_duration': event.get('pause_duration', 0)
        }))


    async def round_ended(self, event):
        """Событие: раунд завершен по таймеру."""
        await self.send(text_data=json.dumps({
            'type': 'round_ended',
            'session_id': event['session_id'],
            'round_number': event['round_number'],
            'reason': event.get('reason', 'unknown'),
            'message': event.get('message', 'Раунд завершен')
        }))

    async def system_message(self, event):
        """Системное сообщение для комнаты."""
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': event['message'],
            'level': event.get('level', 'info')
        }))

    @database_sync_to_async
    def _get_active_session(self):
        """Получить активную игровую сессию для комнаты."""
        from apps.rooms.models import Room

        try:
            room = Room.objects.get(id=self.room_id)
            return room.game_sessions.filter(
                status__in=[
                    GameSession.Status.WAITING,
                    GameSession.Status.PLAYING,
                    GameSession.Status.PAUSED
                ]
            ).first()
        except Room.DoesNotExist:
            return None

    async def send_error(self, message: str):
        """Отправить ошибку клиенту."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    @database_sync_to_async
    def _check_room_exists(self, room_id):
        """Проверить существование комнаты в БД."""
        from apps.rooms.models import Room
        return Room.objects.filter(id=room_id).exists()

    @database_sync_to_async
    def _initialize_room_metadata(self):
        """Инициализировать метаданные комнаты в Redis из БД."""
        from apps.rooms.models import Room
        from apps.game.application.services.websocket_room_service import websocket_room_service

        try:
            room = Room.objects.get(id=self.room_id)
            websocket_room_service.initialize_room_metadata(
                room_id=room.id,
                room_name=room.name,
                status=room.status,
                host_id=room.host_id
            )
        except Room.DoesNotExist:
            pass
