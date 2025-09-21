"""Reusable MQTT bridge starter for management command and optional AppConfig ready()."""
from typing import Optional
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from SmartLight import settings


def start_bridge(broker: Optional[str] = None, port: Optional[int] = None, on_message_extra=None):
    """Start an MQTT client that forwards Devices/macadd/status to Channels.

    This function blocks (calls loop_forever). Call it in a background thread if
    you need non-blocking behavior.
    """
    broker = broker or settings.MQTT_BROKER
    port = port or settings.MQTT_PORT
    channel_layer = get_channel_layer()


    # subscribe to topic i want
    def on_connect(client, userdata, flags, rc):
        print(f"Connected to MQTT broker {broker}:{port} rc={rc}")
        client.subscribe("Devices/+/status")

    # behavior when new message arive from subscribed topic
    def on_message(client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        print(f"MQTT recv {topic} -> {payload}")
        # send it to channel layer
        async_to_sync(channel_layer.send)(
            "mqtt",
            {"type": "mqtt.sub", "text": {"topic": topic, "payload": payload}},
        )
        if on_message_extra:
            try:
                on_message_extra(topic, payload)
            except Exception:
                pass

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port, 60)
    try:
        client.loop_forever()
    finally:
        client.disconnect()
