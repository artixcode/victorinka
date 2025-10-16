from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Room, RoomParticipant

User = get_user_model()

class RoomSerializer(serializers.ModelSerializer):
    host_id = serializers.ReadOnlyField(source="host.id")
    players_count = serializers.SerializerMethodField()

    class Meta:
        ref_name = "RoomPatchSerializer"
        model = Room
        fields = ["id", "name", "host_id", "invite_code", "status", "created_at", "players_count"]
        read_only_fields = ["invite_code", "status", "created_at", "host_id", "players_count"]

    def get_players_count(self, obj):
        return obj.participants.count()

    def create(self, validated_data):
        request = self.context["request"]
        room = Room.objects.create(host=request.user, **validated_data)
        RoomParticipant.objects.create(room=room, user=request.user, role=RoomParticipant.Role.HOST)
        return room


class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["name"]
