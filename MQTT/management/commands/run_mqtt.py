from django.core.management.base import BaseCommand
from MQTT.mqtt_bridge import start_bridge
from SmartLight import settings


class Command(BaseCommand):
    help = "Run MQTT bridge that forwards messages into Django Channels"

    def handle(self, *args, **options):
        broker = settings.MQTT_BROKER
        port =settings.MQTT_PORT
        try:
            start_bridge(broker=broker, port=port)
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("MQTT bridge stopped"))
