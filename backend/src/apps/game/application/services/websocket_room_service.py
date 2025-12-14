from typing import Optional, Dict, List
import re
from apps.game.domain.services.room_session_service import RoomSessionService
from apps.game.infrastructure.redis_room_repository import room_state_repository
from apps.game.models import GameSession
from apps.rooms.models import Room

class WebSocketRoomService:

    MESSAGE_MIN_LENGTH = 1
    MESSAGE_MAX_LENGTH = 500

    def __init__(self):
        self.room_session_service = RoomSessionService(room_state_repository)
        self.repository = room_state_repository

    def initialize_room_metadata(self, room_id: int, room_name: str, status: str, host_id: int) -> None:
        """
        Инициализировать метаданные комнаты в Redis при первом подключении.
        """
        # Проверяем, существуют ли уже метаданные
        existing = self.repository.get_room_metadata(room_id)
        if not existing:
            self.repository.set_room_metadata(
                room_id=room_id,
                room_name=room_name,
                status=status,
                host_id=host_id
            )

    def validate_message(self, message: str) -> tuple[bool, Optional[str]]:
        """
        Валидация сообщения чата.
        """
        if not message or not message.strip():
            return False, "Сообщение не может быть пустым"

        message = message.strip()

        if len(message) < self.MESSAGE_MIN_LENGTH:
            return False, f"Сообщение слишком короткое (минимум {self.MESSAGE_MIN_LENGTH} символ)"

        if len(message) > self.MESSAGE_MAX_LENGTH:
            return False, f"Сообщение слишком длинное (максимум {self.MESSAGE_MAX_LENGTH} символов)"

        # Проверка на спам (только пробелы, символы, эмодзи без текста)
        if not re.search(r'[a-zA-Zа-яА-ЯёЁ0-9]', message):
            return False, "Сообщение должно содержать текст или цифры"

        return True, None


    def handle_player_join(
        self,
        room_id: int,
        user_id: int,
        username: str,
        channel_name: str
    ) -> Dict:
        """
        Обработка присоединения игрока к комнате.
        """
        # Обновляем TTL комнаты при активности
        self.repository.refresh_room_ttl(room_id)

        metadata = self.repository.get_room_metadata(room_id)
        is_host = metadata.get('host_id') == user_id if metadata else False

        # Вызываем domain service
        event = self.room_session_service.join_room(
            room_id=room_id,
            user_id=user_id,
            username=username,
            channel_name=channel_name
        )
        
        # Получаем обновленную информацию о комнате
        room_info = self.room_session_service.get_room_info(room_id)
        
        return {
            'event': 'player_joined',
            'user_id': event.user_id,
            'username': event.username,
            'is_host': is_host,
            'timestamp': event.timestamp.isoformat(),
            'room_info': room_info
        }

    def handle_player_leave(
        self,
        room_id: int,
        user_id: int,
        username: str,
        channel_name: str
    ) -> Dict:
        """
        Обработка выхода игрока из комнаты.
        """
        event = self.room_session_service.leave_room(
            room_id=room_id,
            user_id=user_id,
            username=username,
            channel_name=channel_name
        )
        
        room_info = self.room_session_service.get_room_info(room_id)
        
        return {
            'event': 'player_left',
            'user_id': event.user_id,
            'username': event.username,
            'timestamp': event.timestamp.isoformat(),
            'room_info': room_info
        }

    def handle_chat_message(
        self,
        room_id: int,
        user_id: int,
        username: str,
        message: str
    ) -> Optional[Dict]:
        """
        Обработка сообщения в чате комнаты.
        """
        # Валидация сообщения
        is_valid, error = self.validate_message(message)
        if not is_valid:
            return {
                'error': True,
                'message': error
            }

        # Очистка сообщения
        message = message.strip()[:self.MESSAGE_MAX_LENGTH]

        # Обновляем TTL комнаты при активности
        self.repository.refresh_room_ttl(room_id)

        # Вызываем domain service
        event = self.room_session_service.send_message(
            room_id=room_id,
            user_id=user_id,
            username=username,
            message=message
        )
        
        if not event:
            return None
        
        return {
            'event': 'chat_message',
            'user_id': event.user_id,
            'username': event.username,
            'message': event.message,
            'timestamp': event.timestamp.isoformat()
        }

    def get_room_state(self, room_id: int) -> Dict:
        """
        Получить полное состояние комнаты включая метаданные и текущую игру.
        """
        # Базовая информация
        room_info = self.room_session_service.get_room_info(room_id)

        # Метаданные из Redis
        metadata = self.repository.get_room_metadata(room_id)

        # Объединяем данные
        if metadata:
            room_info.update({
                'room_name': metadata.get('room_name'),
                'status': metadata.get('status'),
                'host_id': metadata.get('host_id'),
                'created_at': metadata.get('created_at')
            })

        # Добавляем последние сообщения
        recent_messages = self.repository.get_recent_messages(room_id, limit=20)
        room_info['recent_messages'] = recent_messages


        try:
            room = Room.objects.get(id=room_id)
            active_session = room.game_sessions.filter(
                status__in=[GameSession.Status.PLAYING, GameSession.Status.WAITING]
            ).order_by('-created_at').first()

            if active_session:
                room_info['game_session'] = {
                    'id': active_session.id,
                    'status': active_session.status,
                    'quiz_title': active_session.quiz.title,
                    'total_questions': active_session.quiz.questions.count()
                }

                # Если игра идет - получаем текущий вопрос из Redis
                if active_session.status == GameSession.Status.PLAYING:
                    from apps.game.infrastructure.redis_game_state_repository import game_state_repository
                    game_state = game_state_repository.get_game_state(active_session.id)
                    current_round = game_state_repository.get_current_round(active_session.id)

                    if current_round:
                        room_info['current_question'] = {
                            'round_number': current_round.get('round_number'),
                            'question_id': current_round.get('question_id'),
                            'question_text': current_round.get('question_text'),
                            'options': current_round.get('options', []),
                            'time_limit': current_round.get('time_limit', 30),
                            'points': current_round.get('points', 0),
                            'difficulty': current_round.get('difficulty', 'medium')
                        }
        except Room.DoesNotExist:
            pass

        return room_info

    def get_players(self, room_id: int) -> List[Dict]:
        """Получить список игроков."""
        return self.room_session_service.get_players_list(room_id)


websocket_room_service = WebSocketRoomService()

