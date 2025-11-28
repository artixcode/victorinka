from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass(frozen=True)
class PlayerInfo:
    """Информация об игроке в комнате."""
    user_id: int
    username: str
    channel_name: str
    joined_at: str

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'joined_at': self.joined_at
        }


@dataclass(frozen=True)
class ChatMessage:
    """Сообщение в чате комнаты."""
    id: str
    user_id: int
    username: str
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'message': self.message,
            'timestamp': self.timestamp
        }


@dataclass(frozen=True)
class RoomState:
    """Состояние игровой комнаты."""
    room_id: int
    room_name: str
    status: str
    host_id: int
    player_count: int
    players: List[PlayerInfo]
    recent_messages: List[ChatMessage]

    def to_dict(self) -> dict:
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'status': self.status,
            'host_id': self.host_id,
            'player_count': self.player_count,
            'players': [p.to_dict() for p in self.players],
            'recent_messages': [m.to_dict() for m in self.recent_messages]
        }


@dataclass(frozen=True)
class RoomMetadata:
    """Метаданные комнаты для хранения в Redis."""
    room_id: int
    room_name: str
    status: str
    host_id: int
    created_at: str

    def to_dict(self) -> dict:
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'status': self.status,
            'host_id': self.host_id,
            'created_at': self.created_at
        }

