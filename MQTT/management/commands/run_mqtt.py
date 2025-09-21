from django.core.management.base import BaseCommand
from MQTT.mqtt_bridge import start_bridge
from django.conf import settings


class Command(BaseCommand):
    help = "Run MQTT bridge that forwards messages into Django Channels"

    def handle(self, *args, **options):
        broker = getattr(settings, "MQTT_BROKER", None)
        port = getattr(settings, "MQTT_PORT", None)
        try:
            start_bridge(broker=broker, port=port)
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("MQTT bridge stopped"))
