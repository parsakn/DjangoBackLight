"""Reusable MQTT bridge starter for management command and optional AppConfig ready()."""
from typing import Optional
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from SmartLight import settings
from Places_Lamp.models import Lamp
import json


def start_bridge(broker: Optional[str] = None, port: Optional[int] = None, on_message_extra=None):
    """Start an MQTT client that forwards Devices/macadd/status to Channels.

    This function blocks (calls loop_forever). Call it in a background thread if
    you need non-blocking behavior.
    """
    broker = broker or settings.MQTT_BROKER
    port = port or settings.MQTT_PORT
    channel_layer = get_channel_layer()
    try:
        print("Channel layer backend:", type(channel_layer), flush=True)
    except Exception:
        pass


    # subscribe to topic i want
    def on_connect(client, userdata, flags, rc):
        print(f"Connected to MQTT broker {broker}:{port} rc={rc}")
        client.subscribe("Devices/+/status")

    # behavior when new message arive from subscribed topic
    def on_message(client, userdata, msg):
        topic = msg.topic
        payload_bytes = msg.payload
        try:
        # decode bytes to string and parse JSON
            payload = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            print("⚠️ Failed to parse payload as JSON, raw:", payload_bytes)
            payload = None
        print(f"MQTT recv {topic} -> {payload}")
        # Try to update Lamp in DB directly so web UI sees changes even if
        # the named-channel consumer doesn't get invoked across processes.
        try:
            token = topic.split("/")[1]
            # interpret simple payloads
            status , establish = None , None
            p = payload.get("msg","")
            e = payload.get("establish","")
            if p in ("1", "on", "ON"):
                status = True
            elif p in ("0", "off", "OFF"):
                status = False
            if e=="Connected" : 
                establish=True
            
            
            if status is not None:
                lamp = Lamp.objects.get(token=token)
                lamp.status = status
                lamp.save(update_fields=["status"])
                # Broadcast to all authorized users of this lamp
                targets = [lamp.room.home.owner]
                targets += list(lamp.shared_with.all())
                targets += list(lamp.room.home.shared_with.all())
                data = {
                    "lamp": lamp.name,
                    "token": str(lamp.token),
                    "status": bool(lamp.status),
                    "raw": payload,
                    "establish": False,
                    "room": getattr(lamp.room, 'name', None),
                }
                for target in targets:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{target.id}", {"type": "lamp.status", "text": data}
                    )
                print("Bridge: updated Lamp and broadcasted to groups", flush=True)
            elif establish is not None : 
                lamp = Lamp.objects.get(token=token)
                lamp.connection = establish
                lamp.save(update_fields=["connection"])
                # Broadcast to all authorized users of this lamp
                targets = [lamp.room.home.owner]
                targets += list(lamp.shared_with.all())
                targets += list(lamp.room.home.shared_with.all())
                data = {
                    "lamp": lamp.name,
                    "token": str(lamp.token),
                    "status": bool(lamp.status),
                    "raw": payload,
                    "establish": True,
                    "room": getattr(lamp.room, 'name', None),
                }
                for target in targets:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{target.id}", {"type": "lamp.connection", "text": data}
                    )
                print("Bridge: updated Lamp and broadcasted to groups", flush=True)
        
        except Exception as _e:
            # Non-fatal: continue to also send the raw message into the channel layer
            print("Bridge: failed direct DB update/broadcast:", _e , flush=True)

        # Always forward the raw message into the named 'mqtt' channel so
        # existing SyncConsumer/MqttConsumer can pick it up if available.
        try:
            print("Bridge sending to channel 'mqtt'", flush=True)
            async_to_sync(channel_layer.send)(
                "mqtt",
                {"type": "mqtt.sub", "text": {"topic": topic, "payload": payload}},
            )
            print("Bridge channel send completed", flush=True)
        except Exception as e:
            print("⚠️ Bridge failed to send to channel layer:", e, flush=True)
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
