from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RoomEvent:
    """Базовое событие комнаты."""
    room_id: int
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            from django.utils import timezone
            self.timestamp = timezone.now()


@dataclass
class PlayerJoinedRoom(RoomEvent):
    """Событие: игрок присоединился к комнате."""
    user_id: int = 0
    username: str = ""
    channel_name: str = ""


@dataclass
class PlayerLeftRoom(RoomEvent):
    """Событие: игрок покинул комнату."""
    user_id: int = 0
    username: str = ""
    channel_name: str = ""


@dataclass
class RoomMessageSent(RoomEvent):
    """Событие: сообщение в чате комнаты."""
    user_id: int = 0
    username: str = ""
    message: str = ""
    message_id: Optional[str] = None


@dataclass
class GameStatusChanged(RoomEvent):
    """Событие: статус игры изменился."""
    old_status: str = ""
    new_status: str = ""
    session_id: Optional[int] = None

