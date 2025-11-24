import json
from typing import List
from django.core.cache import cache
from apps.game.domain.repositories import IRoomStateRepository


class RedisRoomStateRepository(IRoomStateRepository):  # type: ignore[misc]
    """
    Хранение состояния комнаты в Redis.
    """

    PLAYER_KEY_TEMPLATE = "room:{room_id}:players"
    MESSAGE_KEY_TEMPLATE = "room:{room_id}:messages"
    MAX_MESSAGES = 100

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
        if not isinstance(messages, list):
            messages = []

        messages.append(message_data)

        # Ограничиваем размер истории
        if len(messages) > self.MAX_MESSAGES:
            messages = messages[-self.MAX_MESSAGES:]

        cache.set(key, messages, timeout=None)

    def get_recent_messages(self, room_id: int, limit: int = 50) -> List[dict]:
        """Получить последние N сообщений чата."""
        key = self._get_message_key(room_id)
        messages = cache.get(key, [])

        if not isinstance(messages, list):
            return []

        # Возвращаем последние N сообщений
        return messages[-limit:]

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

    def bulk_create(self, stats_list: List) -> None:
        pass


room_state_repository = RedisRoomStateRepository()

