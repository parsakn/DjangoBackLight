"""
ASGI config for SmartLight project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.routing import ChannelNameRouter
import MQTT.routing as mqtt_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartLight.settings')

application = ProtocolTypeRouter(
	{
		"http": get_asgi_application(),
		"websocket": URLRouter(mqtt_routing.websocket_urlpatterns),
		"channel": mqtt_routing.channel_routing,
	}
)
