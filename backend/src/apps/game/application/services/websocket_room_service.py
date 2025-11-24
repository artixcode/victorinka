from typing import Optional, Dict, List
from apps.game.domain.services.room_session_service import RoomSessionService
from apps.game.infrastructure.redis_room_repository import room_state_repository


class WebSocketRoomService:


    def __init__(self):
        self.room_session_service = RoomSessionService(room_state_repository)

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
        Получить текущее состояние комнаты.
        """
        return self.room_session_service.get_room_info(room_id)

    def get_players(self, room_id: int) -> List[Dict]:
        """Получить список игроков."""
        return self.room_session_service.get_players_list(room_id)


websocket_room_service = WebSocketRoomService()

