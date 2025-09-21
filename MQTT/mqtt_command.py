import json
from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from SmartLight import settings


# The `Command` class is well-structured and correctly inherits from BaseCommand.
class Command(BaseCommand):
    help = "Run MQTT bridge that forwards messages into Django Channels"

    # The `handle` method is the main entry point for the Django command.
    def handle(self, *args, **options):
        # Good practice: Get the channel layer here, as it's the main dependency
        # for sending messages.
        channel_layer = get_channel_layer()

        # The `client` object is correctly instantiated and configured.
        client = mqtt.Client()

        # We'll create a single `on_message` method that has access to the channel_layer.
        # This avoids using a separate nested function or passing `self` down.
        def on_message_handler(client, userdata, msg):
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            self.stdout.write(f"MQTT recv {topic} -> {payload}")

            # Use async_to_sync to correctly bridge from the synchronous MQTT library
            # to the asynchronous Channels layer.
            # This is a key part of the bridge logic and it's implemented correctly.
            async_to_sync(channel_layer.send)(
                "mqtt",
                {
                    "type": "mqtt.sub",
                    "text": {"topic": topic, "payload": payload},
                },
            )

        client.on_connect = self.on_connect
        client.on_message = on_message_handler
        # Suggestion: Add an on_disconnect callback for more robust logging and
        # to handle reconnections if needed.
        client.on_disconnect = self.on_disconnect

        try:
            self.stdout.write(self.style.NOTICE("Attempting to connect to MQTT broker..."))
            client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            
            # The `loop_forever` method is perfect for a long-running management command.
            client.loop_forever()

        except ConnectionRefusedError:
            self.stdout.write(self.style.ERROR("Connection to MQTT broker refused. Please check the broker's status and connection details."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))
        finally:
            client.disconnect()
            self.stdout.write(self.style.NOTICE("MQTT bridge stopped"))

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.stdout.write(self.style.SUCCESS(f"Connected to MQTT broker {settings.MQTT_BROKER}:{settings.MQTT_PORT}"))
            client.subscribe("Devices/+/status")
        else:
            self.stdout.write(self.style.ERROR(f"Failed to connect to MQTT broker, return code {rc}"))

    def on_disconnect(self, client, userdata, rc):
        # A good practice is to log the disconnection reason.
        if rc != 0:
            self.stdout.write(self.style.WARNING("Disconnected unexpectedly. Attempting to reconnect..."))
            # Here you could implement a reconnection strategy.
