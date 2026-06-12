from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/trip/(?P<room_name>\d+)/$", consumers.ChatConsumer.as_asgi()),
]