from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Room, RoomParticipant

User = get_user_model()


class ParticipantSerializer(serializers.ModelSerializer):
    """Сериализатор для участника комнаты"""
    user_id = serializers.ReadOnlyField(source='user.id')
    nickname = serializers.ReadOnlyField(source='user.nickname')
    username = serializers.ReadOnlyField(source='user.nickname')  # Для совместимости с фронтом
    email = serializers.ReadOnlyField(source='user.email')
    is_host = serializers.SerializerMethodField()

    class Meta:
        model = RoomParticipant
        fields = ['user_id', 'nickname', 'username', 'email', 'role', 'is_host', 'joined_at']

    def get_is_host(self, obj):
        """Проверяем, является ли участник хостом"""
        return obj.role == RoomParticipant.Role.HOST


class RoomSerializer(serializers.ModelSerializer):
    host_id = serializers.ReadOnlyField(source="host.id")
    players_count = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    current_session_id = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["id", "name", "host_id", "invite_code", "status", "created_at", "players_count", "participants", "current_session_id"]
        read_only_fields = ["invite_code", "status", "created_at", "host_id", "players_count", "participants", "current_session_id"]

    def get_players_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'participants' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['participants'])
        return obj.participants.count()

    def get_participants(self, obj):
        """Возвращаем список участников"""
        if hasattr(obj, '_prefetched_objects_cache') and 'participants' in obj._prefetched_objects_cache:
            participants = obj._prefetched_objects_cache['participants']
        else:
            participants = obj.participants.select_related('user').all()

        return ParticipantSerializer(participants, many=True).data

    def get_current_session_id(self, obj):
        """Возвращаем ID текущей активной игровой сессии"""
        from apps.game.models import GameSession
        active_session = obj.game_sessions.filter(
            status__in=[GameSession.Status.PLAYING, GameSession.Status.WAITING]
        ).order_by('-created_at').first()
        return active_session.id if active_session else None

class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["name"]

class RoomPatchSerializer(RoomSerializer):
    class Meta(RoomSerializer.Meta):
        ref_name = "RoomPatchSerializer"  # важно для drf_yasg
        read_only_fields = ["invite_code", "created_at", "host_id", "players_count", "participants", "current_session_id"]
        fields = ["id", "name", "status", "invite_code", "created_at", "host_id", "players_count", "participants", "current_session_id"]
