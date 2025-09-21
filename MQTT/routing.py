from django.urls import re_path
from channels.routing import ChannelNameRouter
from . import consumers


websocket_urlpatterns = [
    re_path(r"ws/light/$", consumers.LightConsumer.as_asgi()),
]


# Channel routing maps a channel name (string) to an ASGI application
channel_routing = ChannelNameRouter(
    {
        "mqtt": consumers.MqttConsumer.as_asgi(),
    }
)
