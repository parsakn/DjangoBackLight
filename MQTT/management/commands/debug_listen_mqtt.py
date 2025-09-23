from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
import json


class Command(BaseCommand):
    help = "Listen for messages sent to the named channel 'mqtt' and print them (debug)"

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        self.stdout.write(f"Using channel layer: {type(channel_layer)}")
        try:
            while True:
                # channel_layer.receive is a coroutine that returns a message dict or None
                try:
                    message = async_to_sync(channel_layer.receive)("mqtt")
                except NotImplementedError:
                    self.stdout.write("channel_layer.receive not implemented for this backend")
                    return

                if message is None:
                    # no message currently; sleep briefly and retry
                    time.sleep(0.2)
                    continue

                # Pretty-print the message
                try:
                    self.stdout.write("Received message on 'mqtt':")
                    self.stdout.write(json.dumps(message, default=str))
                except Exception:
                    self.stdout.write(repr(message))

        except KeyboardInterrupt:
            self.stdout.write("Stopped debug listener")
