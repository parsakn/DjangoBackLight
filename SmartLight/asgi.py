"""
ASGI config for SmartLight project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
import MQTT.routing as mqtt_routing
import MQTT.consumers as mqtt_consumers
from .channels_jwt_middleware import JWTAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartLight.settings')
try:
	# show what channel routing is being used at ASGI startup (debug)
	print("ASGI starting. MQTT routing module:", mqtt_routing, flush=True)
except Exception:
	pass

application = ProtocolTypeRouter(
	{
		"http": get_asgi_application(),
		"websocket": JWTAuthMiddlewareStack(URLRouter(mqtt_routing.websocket_urlpatterns)),
		# Inline ChannelNameRouter here to avoid import-order / registration surprises.
		"channel": ChannelNameRouter({
			"mqtt": mqtt_consumers.MqttConsumer.as_asgi(),
		}),
	}
)
