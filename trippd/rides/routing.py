from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/trip/(?P<room_name>\d+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(
        r"ws/direct/(?P<conversation_id>\d+)/$",
        consumers.DirectMessageConsumer.as_asgi(),
    ),
    re_path(
        r"ws/notifications/(?P<user_id>\d+)/$", consumers.NotificationConsumer.as_asgi()
    ),
]
