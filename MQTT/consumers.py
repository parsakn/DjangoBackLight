from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
import paho.mqtt.publish as publish
from Places_Lamp.models import Lamp
from SmartLight import settings

BROKER_URL = settings.MQTT_BROKER


class MqttConsumer(SyncConsumer):
    """
    Handles MQTT messages (subscribe + publish).
    """
    @staticmethod
    def parse_bool(p):
        """
        Robustly parse a payload into boolean True/False or None (unknown).

        Accepts:
        - plain strings: "ON", "OFF", "1", "0"
        - JSON encoded payloads like '{"msg":"ON"}', '{"status": true}', etc.
        - numeric values 1/0
        - boolean values
        """
        import json

        if p is None:
            return None

        # If it's already a bool
        if isinstance(p, bool):
            return p

        # If it's numeric
        if isinstance(p, (int, float)):
            return bool(p)

        # If it's bytes, decode
        if isinstance(p, bytes):
            try:
                p = p.decode('utf-8')
            except Exception:
                p = str(p)

        # Try to parse JSON
        if isinstance(p, str):
            s = p.strip()
            # try JSON
            try:
                obj = json.loads(s)
                # if dict, try common keys
                if isinstance(obj, dict):
                    for key in ('status', 'state', 'value', 'msg'):
                        if key in obj:
                            return MqttConsumer.parse_bool(obj[key])
                    # nothing recognized
                    return None
                # primitive JSON like true/false/1/"ON"
                return MqttConsumer.parse_bool(obj)
            except Exception:
                pass

            low = s.lower()
            if low in ("1", "true", "on"):
                return True
            if low in ("0", "false", "off"):
                return False
            # lenient matches like 'onn' or 'on\n'
            if low.startswith("on"):
                return True
            if low.startswith("off"):
                return False

        # fallback
        return None
        

    def default(self, event):
        print("🔥 default() caught event:", event, flush=True)
    
    def mqtt_sub(self, event):
        topic = event['text']['topic']
        payload = event['text']['payload']
        print("mqtt_sub" , flush=True)
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
        print("in mqtt publish", flush=True)
        user_id = event.get("user")  # user id passed from WebSocket consumer
        token = event['text']['token']
        payload = event['text']['payload']

        try:
            lamp = Lamp.objects.get(token=token)
        except Lamp.DoesNotExist:
            print("⚠️ Invalid lamp token")
            return

        # resolve user from id (safe across channel layer boundaries)
        if user_id is None:
            print("❌ mqtt_pub called without user id")
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            print("❌ mqtt_pub: user not found")
            return

        if not lamp.can_access(user):
            print(f"❌ Unauthorized publish attempt by {user.username} for lamp {lamp.name}")
            return

        topic = f"Devices/{token}/command"
        print(f"MQTT PUB → {user.username} → {topic}={payload}", flush=True)

        try:
            publish.single(topic, payload, hostname=BROKER_URL)
        except Exception as e:
            # keep consumer resilient and log publish errors
            print("⚠️ MQTT publish failed:", e, flush=True)
        
class LightConsumer(AsyncJsonWebsocketConsumer):

    @staticmethod
    def parse_bool(p):
        if(p=="1" or p=="on" or p=="ON") : 
            return True 
        elif (p=="0" or p=="off" or p=="OFF"):
            return False
        else : 
            return None

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
        print("in recive Json")
        token = content.get("token")
        payload = content.get("payload")  # e.g., "ON" / "OFF"
        # send through channel layer to 'mqtt' channel (SyncConsumer)
        # send user id (serializable) to the channel layer; resolve user in mqtt_pub
        print("user id : ",getattr(self.scope.get("user"), "id", None))
        try:
            print("sending to channel 'mqtt' ->", token, payload)
            await self.channel_layer.send(
                "mqtt",
                {
                    "type": "mqtt.pub",
                    "user": getattr(self.scope.get("user"), "id", None),
                    "text": {"token": token, "payload": payload},
                },
            )
            print("channel send completed")
        except Exception as e:
            print("⚠️ channel send failed:", e)

        # Also update DB and broadcast immediately so all shared users see the change
        # without waiting for the MQTT roundtrip from the device.
        async def _update_and_broadcast():
            user = self.scope.get("user")
            try:
                lamp = await sync_to_async(Lamp.objects.get)(token=token)
            except Lamp.DoesNotExist:
                return

            # Check authorization
            can = await sync_to_async(lamp.can_access)(user)
            if not can:
                return

            parsed = LightConsumer.parse_bool(payload)
            if parsed is not None:
                # save status
                await sync_to_async(lambda: lamp.__class__.objects.filter(pk=lamp.pk).update(status=parsed))()

            # prepare targets: owner, lamp.shared_with, home.shared_with
            owner = lamp.room.home.owner
            targets = [owner]
            targets += list(await sync_to_async(list)(lamp.shared_with.all()))
            targets += list(await sync_to_async(list)(lamp.room.home.shared_with.all()))

            data = {
                "lamp": lamp.name,
                "token": str(lamp.token),
                "status": bool(parsed) if parsed is not None else bool(lamp.status),
                "raw": payload,
            }

            for target in targets:
                await self.channel_layer.group_send(f"user_{target.id}", {"type": "lamp.status", "text": data})

            # Fallback: publish directly from the websocket path if channel routing
            # to the named 'mqtt' consumer doesn't reach the SyncConsumer for any reason.
            # Do this after authorization and DB update to avoid security issues.
            try:
                topic = f"Devices/{token}/command"
                # Use sync_to_async to avoid blocking the event loop
                await sync_to_async(publish.single)(topic, payload, hostname=BROKER_URL)
                print(f"Fallback MQTT PUB → {topic}={payload}", flush=True)
            except Exception as e:
                print("⚠️ Fallback MQTT publish failed:", e, flush=True)

        await _update_and_broadcast()

    async def lamp_status(self, event):
        """
        Updates coming from MQTT (via MqttConsumer).
        """
        await self.send_json(event["text"])
