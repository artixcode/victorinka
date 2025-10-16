from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Room, RoomParticipant

User = get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    host_id = serializers.ReadOnlyField(source="host.id")
    players_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["id", "name", "host_id", "invite_code", "status", "created_at", "players_count"]
        read_only_fields = ["invite_code", "status", "created_at", "host_id", "players_count"]

    def get_players_count(self, obj):
        return obj.participants.count()

class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["name"]

class RoomPatchSerializer(RoomSerializer):
    class Meta(RoomSerializer.Meta):
        ref_name = "RoomPatchSerializer"  # важно для drf_yasg
        read_only_fields = ["invite_code", "created_at", "host_id", "players_count"]
        fields = ["id", "name", "status", "invite_code", "created_at", "host_id", "players_count"]
