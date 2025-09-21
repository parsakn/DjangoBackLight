from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
import paho.mqtt.publish as publish
from Places_Lamp.models import Lamp

BROKER_URL = "mqtt.example.com"


class MqttConsumer(SyncConsumer):
    """
    Handles MQTT messages (subscribe + publish).
    """
    @classmethod
    def parse_bool(p):
        if(p=="1" or p=="on") : 
            return True 
        elif (p=="0" or p=="off"):
            return False
        else : 
            return None
    def mqtt_sub(self, event):
        topic = event['text']['topic']
        payload = event['text']['payload']

        # Extract lamp token from topic
        try:
            # here token means mac address 

            token = topic.split("/")[1]  
            lamp = Lamp.objects.get(token=token)
            # lamp.owner doesn't exist; owner is room.home.owner
            user = lamp.room.home.owner
        except Lamp.DoesNotExist:
            print("⚠️ Unknown lamp token in topic:", topic)
            return

        print(f"MQTT SUB → Lamp {lamp.name} ({user.username}) status={payload}")

        # Try to interpret common payload formats as boolean


        parsed = MqttConsumer.parse_bool(payload)
        if parsed is not None:
            try:
                lamp.status = parsed
                lamp.save(update_fields=["status"])
            except Exception as e:
                print("⚠️ Failed to save lamp status:", e)

        # Broadcast to all authorized users of this lamp
        # collect targets: home owner, lamp.shared_with, home.shared_with
        targets = [lamp.room.home.owner]
        targets += list(lamp.shared_with.all())
        targets += list(lamp.room.home.shared_with.all())

        for target in targets:
            async_to_sync(self.channel_layer.group_send)(
                f"user_{target.id}",
                {
                    "type": "lamp.status",
                    "text": {
                        "lamp": lamp.name,
                        "token": str(lamp.token),
                        "status": bool(lamp.status),
                        "raw": payload,
                    },
                },
            )

    def mqtt_pub(self, event):
        """
        Publish only if the requesting user is authorized.
        """
        user = event.get("user")  # must be passed from WebSocket
        token = event['text']['token']
        payload = event['text']['payload']

        try:
            lamp = Lamp.objects.get(token=token)
        except Lamp.DoesNotExist:
            print("⚠️ Invalid lamp token")
            return
        # ensure user is authorized
        if user is None:
            print("❌ mqtt_pub called without user")
            return

        if not lamp.can_access(user):
            print(f"❌ Unauthorized publish attempt by {user.username} for lamp {lamp.name}")
            return

        topic = f"smartlight/control/{lamp.token}"
        print(f"MQTT PUB → {user.username} → {topic}={payload}")

        publish.single(topic, payload, hostname=BROKER_URL)
        
class LightConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_add(f"user_{user.id}", self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)

    async def receive_json(self, content):
        """
        User wants to toggle lamp
        """
        token = content.get("token")
        payload = content.get("payload")  # e.g., "ON" / "OFF"
        # send through channel layer to 'mqtt' channel (SyncConsumer)
        await self.channel_layer.send(
            "mqtt",
            {
                "type": "mqtt.pub",
                "user": self.scope["user"],
                "text": {"token": token, "payload": payload},
            },
        )

    async def lamp_status(self, event):
        """
        Updates coming from MQTT (via MqttConsumer).
        """
        await self.send_json(event["text"])
