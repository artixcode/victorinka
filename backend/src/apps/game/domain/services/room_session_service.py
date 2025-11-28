from typing import Optional, List, Dict
from apps.game.domain.repositories import IRoomStateRepository
from apps.game.domain.events.room_events import (
    PlayerJoinedRoom,
    PlayerLeftRoom,
    RoomMessageSent
)


class RoomSessionService:
    """
    Доменный сервис для управления сессией комнаты (WebSocket).
    """

    def __init__(self, room_state_repo: IRoomStateRepository):
        self.room_state_repo = room_state_repo

    def join_room(
        self,
        room_id: int,
        user_id: int,
        username: str,
        channel_name: str
    ) -> PlayerJoinedRoom:
        """
        Игрок присоединяется к комнате.
        """
        # Проверяем, не в комнате ли уже
        already_in = self.room_state_repo.is_player_in_room(room_id, user_id)
        
        if already_in:
            # Обновляем channel_name (переподключение)
            self.room_state_repo.remove_player(room_id, user_id)
        
        # Добавляем игрока
        self.room_state_repo.add_player(room_id, user_id, username, channel_name)
        
        # Создаём событие
        event = PlayerJoinedRoom(
            room_id=room_id,
            user_id=user_id,
            username=username,
            channel_name=channel_name
        )
        
        return event

    def leave_room(
        self,
        room_id: int,
        user_id: int,
        username: str,
        channel_name: str
    ) -> PlayerLeftRoom:
        """
        Игрок покидает комнату.
        """
        # Удаляем из Redis
        self.room_state_repo.remove_player(room_id, user_id)
        
        # Создаём событие
        event = PlayerLeftRoom(
            room_id=room_id,
            user_id=user_id,
            username=username,
            channel_name=channel_name
        )
        
        return event

    def send_message(
        self,
        room_id: int,
        user_id: int,
        username: str,
        message: str
    ) -> Optional[RoomMessageSent]:
        """
        Отправка сообщения в чат комнаты.
        """
        # Проверяем, что игрок в комнате
        if not self.room_state_repo.is_player_in_room(room_id, user_id):
            return None
        
        # Валидация сообщения
        message = message.strip()
        if not message or len(message) > 500:
            return None
        
        # Сохраняем в Redis
        self.room_state_repo.add_message(room_id, user_id, username, message)
        
        # Создаём событие
        event = RoomMessageSent(
            room_id=room_id,
            user_id=user_id,
            username=username,
            message=message
        )
        
        return event

    def get_room_info(self, room_id: int) -> Dict:
        """
        Получить информацию о текущем состоянии комнаты.
        """
        players = self.room_state_repo.get_players(room_id)
        player_count = self.room_state_repo.get_player_count(room_id)
        recent_messages = self.room_state_repo.get_recent_messages(room_id, limit=20)
        
        return {
            'room_id': room_id,
            'player_count': player_count,
            'players': players,
            'recent_messages': recent_messages
        }

    def get_players_list(self, room_id: int) -> List[Dict]:
        """Получить список игроков в комнате."""
        return self.room_state_repo.get_players(room_id)

