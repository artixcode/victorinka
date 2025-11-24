from django.urls import path, re_path
from apps.game.consumers import GameRoomConsumer

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_id>\d+)/$', GameRoomConsumer.as_asgi()),
]

