import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


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
        self.username = self.user.username or self.user.email

        # Проверяем существование комнаты
        room_exists = await self._check_room_exists(self.room_id)
        if not room_exists:
            await self.close(code=4004)
            return

        # Принимаем соединение
        await self.accept()

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
