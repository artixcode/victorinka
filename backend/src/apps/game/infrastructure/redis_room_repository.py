import json
from typing import List, Optional
from django.core.cache import cache
from apps.game.domain.repositories import IRoomStateRepository


class RedisRoomStateRepository(IRoomStateRepository):  # type: ignore[misc]
    """
    Хранение состояния комнаты в Redis.
    """

    METADATA_KEY_TEMPLATE = "room:{room_id}:metadata"
    PLAYER_KEY_TEMPLATE = "room:{room_id}:players"
    MESSAGE_KEY_TEMPLATE = "room:{room_id}:messages"

    MAX_MESSAGES = 100
    ROOM_TTL = 3600 * 24
    MESSAGE_MAX_LENGTH = 500

    def _get_metadata_key(self, room_id: int) -> str:
        return self.METADATA_KEY_TEMPLATE.format(room_id=room_id)

    def _get_player_key(self, room_id: int) -> str:
        return self.PLAYER_KEY_TEMPLATE.format(room_id=room_id)

    def _get_message_key(self, room_id: int) -> str:
        return self.MESSAGE_KEY_TEMPLATE.format(room_id=room_id)

    def add_player(self, room_id: int, user_id: int, username: str, channel_name: str) -> None:
        """Добавить игрока в комнату."""
        from django.utils import timezone

        key = self._get_player_key(room_id)
        player_data = {
            'user_id': user_id,
            'username': username,
            'channel_name': channel_name,
            'joined_at': timezone.now().isoformat()
        }

        cache_key = f"{key}:{user_id}"
        cache.set(cache_key, json.dumps(player_data), timeout=None)

        set_key = f"{key}:set"
        current_set = cache.get(set_key, set())
        if not isinstance(current_set, set):
            current_set = set()
        current_set.add(user_id)
        cache.set(set_key, current_set, timeout=None)

    def remove_player(self, room_id: int, user_id: int) -> None:
        """Удалить игрока из комнаты."""
        key = self._get_player_key(room_id)
        cache_key = f"{key}:{user_id}"
        cache.delete(cache_key)

        set_key = f"{key}:set"
        current_set = cache.get(set_key, set())
        if isinstance(current_set, set) and user_id in current_set:
            current_set.remove(user_id)
            cache.set(set_key, current_set, timeout=None)

    def get_players(self, room_id: int) -> List[dict]:
        """Получить список всех игроков в комнате."""
        key = self._get_player_key(room_id)
        set_key = f"{key}:set"
        user_ids = cache.get(set_key, set())

        if not isinstance(user_ids, set):
            return []

        players = []
        for user_id in user_ids:
            cache_key = f"{key}:{user_id}"
            player_json = cache.get(cache_key)
            if player_json:
                try:
                    player_data = json.loads(player_json)
                    players.append(player_data)
                except json.JSONDecodeError:
                    continue

        return players

    def get_player_count(self, room_id: int) -> int:
        """Получить количество игроков в комнате."""
        key = self._get_player_key(room_id)
        set_key = f"{key}:set"
        user_ids = cache.get(set_key, set())

        if not isinstance(user_ids, set):
            return 0

        return len(user_ids)

    def is_player_in_room(self, room_id: int, user_id: int) -> bool:
        """Проверить, находится ли игрок в комнате."""
        key = self._get_player_key(room_id)
        set_key = f"{key}:set"
        user_ids = cache.get(set_key, set())

        if not isinstance(user_ids, set):
            return False

        return user_id in user_ids

    def add_message(self, room_id: int, user_id: int, username: str, message: str) -> None:
        """Добавить сообщение в чат комнаты."""
        from django.utils import timezone
        import uuid
        import logging

        logger = logging.getLogger(__name__)
        key = self._get_message_key(room_id)

        message_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'username': username,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }

        # Получаем текущий список сообщений
        messages = cache.get(key, [])
        logger.info(f"💾 add_message: current messages count: {len(messages) if isinstance(messages, list) else 'N/A'}")

        if not isinstance(messages, list):
            messages = []

        messages.append(message_data)
        logger.info(f"✅ add_message: appended, new count: {len(messages)}")

        # Ограничиваем размер истории
        if len(messages) > self.MAX_MESSAGES:
            messages = messages[-self.MAX_MESSAGES:]

        cache.set(key, messages, timeout=None)
        logger.info(f"💾 add_message: saved to Redis with key={key}")

    def get_recent_messages(self, room_id: int, limit: int = 50) -> List[dict]:
        """Получить последние N сообщений чата."""
        key = self._get_message_key(room_id)
        messages = cache.get(key, [])

        # Отладка
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 get_recent_messages: key={key}, type={type(messages)}, len={len(messages) if isinstance(messages, list) else 'N/A'}")

        if not isinstance(messages, list):
            logger.warning(f"⚠️ messages is not a list: {type(messages)}")
            return []

        # Возвращаем последние N сообщений
        result = messages[-limit:]
        logger.info(f"✅ Returning {len(result)} messages")
        return result

    def clear_room(self, room_id: int) -> None:
        """Очистить всё состояние комнаты."""
        # Удаляем игроков
        player_key = self._get_player_key(room_id)
        set_key = f"{player_key}:set"
        user_ids = cache.get(set_key, set())

        if isinstance(user_ids, set):
            for user_id in user_ids:
                cache.delete(f"{player_key}:{user_id}")

        cache.delete(set_key)

        # Удаляем сообщения
        message_key = self._get_message_key(room_id)
        cache.delete(message_key)

        # Удаляем метаданные
        metadata_key = self._get_metadata_key(room_id)
        cache.delete(metadata_key)

    def set_room_metadata(self, room_id: int, room_name: str, status: str, host_id: int) -> None:
        """Сохранить метаданные комнаты в Redis."""
        from django.utils import timezone

        metadata_key = self._get_metadata_key(room_id)
        metadata = {
            'room_id': room_id,
            'room_name': room_name,
            'status': status,
            'host_id': host_id,
            'created_at': timezone.now().isoformat()
        }
        cache.set(metadata_key, json.dumps(metadata), timeout=self.ROOM_TTL)

    def get_room_metadata(self, room_id: int) -> Optional[dict]:
        """Получить метаданные комнаты из Redis."""
        metadata_key = self._get_metadata_key(room_id)
        metadata_json = cache.get(metadata_key)

        if not metadata_json:
            return None

        try:
            return json.loads(metadata_json)
        except json.JSONDecodeError:
            return None

    def update_room_status(self, room_id: int, status: str) -> None:
        """Обновить статус комнаты."""
        metadata = self.get_room_metadata(room_id)
        if metadata:
            metadata['status'] = status
            metadata_key = self._get_metadata_key(room_id)
            cache.set(metadata_key, json.dumps(metadata), timeout=self.ROOM_TTL)

    def room_exists(self, room_id: int) -> bool:
        """Проверить существование комнаты в Redis."""
        metadata_key = self._get_metadata_key(room_id)
        return cache.get(metadata_key) is not None

    def refresh_room_ttl(self, room_id: int) -> None:
        """Обновить TTL комнаты (продлить время жизни)."""
        metadata_key = self._get_metadata_key(room_id)
        metadata = cache.get(metadata_key)
        if metadata:
            cache.set(metadata_key, metadata, timeout=self.ROOM_TTL)

    def bulk_create(self, stats_list: List) -> None:
        pass


room_state_repository = RedisRoomStateRepository()

