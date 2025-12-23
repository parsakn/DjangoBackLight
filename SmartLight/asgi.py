"""
ASGI config for SmartLight project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# IMPORTANT: Set settings and initialize Django BEFORE importing any models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartLight.settings')

from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import models.
django_asgi_app = get_asgi_application()

# Now it's safe to import modules that use models
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
import MQTT.routing as mqtt_routing
import MQTT.consumers as mqtt_consumers
from .channels_jwt_middleware import JWTAuthMiddlewareStack

try:
    # show what channel routing is being used at ASGI startup (debug)
    print("ASGI starting. MQTT routing module:", mqtt_routing, flush=True)
except Exception:
    pass

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(mqtt_routing.websocket_urlpatterns)),
        # Inline ChannelNameRouter here to avoid import-order / registration surprises.
        "channel": ChannelNameRouter({
            "mqtt": mqtt_consumers.MqttConsumer.as_asgi(),
        }),
    }
)
