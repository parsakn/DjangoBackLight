from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
import paho.mqtt.publish as publish
from Places_Lamp.models import Lamp
from SmartLight import settings
from django.contrib.auth import get_user_model # Added
import json # Added to ensure send_initial_lamp_status can use it if needed

BROKER_URL = settings.MQTT_BROKER
User = get_user_model() # Added


class MqttConsumer(SyncConsumer):
    # ... (Keep your MqttConsumer class as is, for brevity)
    @staticmethod
    def parse_bool(p):
        if(p=="1" or p=="on" or p=="ON") : 
            return True 
        elif (p=="0" or p=="off" or p=="OFF"):
            return False
        else : 
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
                        # Pass connection status on subscription, though device-initiated updates
                        # typically mean connection is established. This is for full sync.
                        "establish": lamp.connection, 
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

    # --- New Function: Fetching Lamps Asynchronously ---
    @sync_to_async
    def get_user_lamps_for_sync(self):
        """Retrieves all unique lamps owned by or shared with the user."""
        user = self.scope["user"]
        
        owned_homes = user.places.all()
        owned_lamps_list = []
        for home in owned_homes:
            for room in home.rooms.all():
                owned_lamps_list.extend(list(room.lamps.select_related('room__home').all())) # Added select_related for efficiency
        
        shared_lamps_qs = user.shared_lamps.select_related('room__home').all()
        
        # Deduplicate and return unique lamps
        return {
            l.id: l 
            for l in (owned_lamps_list + list(shared_lamps_qs))
        }.values()

    # --- New Function: Sending Initial State ---
    async def send_initial_lamp_status(self):
        """Sends the current established status for all lamps to the client."""
        all_lamps = await self.get_user_lamps_for_sync()
        
        for lamp in all_lamps:
            # Payload tailored to the client-side JS logic
            payload = {
                "token": str(lamp.token),
                "status": bool(lamp.status),
                "lamp": lamp.name,
                "room": lamp.room.name,
                # CRITICAL: This flag tells the JS where to put the row (Established vs. Unestablished)
                "establish": lamp.connection 
            }
            
            # Use self.send_json for sending to the current client
            await self.send_json(payload)
            
        print(f"Sent initial state for {len(all_lamps)} lamps to {self.scope['user'].username}.")


    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.user_group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            await self.accept()
            
            # CRITICAL ADDITION: Re-synchronize state upon connection/reconnection
            await self.send_initial_lamp_status()
            
        else:
            await self.close()

    async def disconnect(self, code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)

    async def receive_json(self, content):
        # ... (Keep receive_json logic mostly as is, but ensure lamp.connection is passed in the broadcast)
        token = content.get("token")
        payload = content.get("payload")  # e.g., "ON" / "OFF"
        
        # send through channel layer to 'mqtt' channel (SyncConsumer)
        try:
            await self.channel_layer.send(
                "mqtt",
                {
                    "type": "mqtt.pub",
                    "user": getattr(self.scope.get("user"), "id", None),
                    "text": {"token": token, "payload": payload},
                },
            )
        except Exception as e:
            print("⚠️ channel send failed:", e)

        # Also update DB and broadcast immediately (Optimistic Update)
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
                # CRITICAL: Always pass the current connection status in broadcasts
                "establish": lamp.connection, 
            }

            for target in targets:
                await self.channel_layer.group_send(f"user_{target.id}", {"type": "lamp.status", "text": data})

            # Fallback MQTT PUB logic...
            try:
                topic = f"Devices/{token}/command"
                await sync_to_async(publish.single)(topic, payload, hostname=BROKER_URL)
                print(f"Fallback MQTT PUB → {topic}={payload}", flush=True)
            except Exception as e:
                print("⚠️ Fallback MQTT publish failed:", e, flush=True)

        await _update_and_broadcast()

    async def lamp_status(self, event):
        """
        Updates coming from MQTT (via MqttConsumer).
        """
        text = event.get("text") or {}
        # The payload now includes 'establish', which the JS handles correctly.
        try:
            await self.send_json(text)
        except Exception as e:
            try:
                print("⚠️ send_json failed, error:", e, "payload:", repr(text), flush=True)
            except Exception:
                pass
            # Ensure the minimal safe payload also includes 'establish' if possible
            safe = {
                "token": text.get("token"), 
                "status": bool(text.get("status")),
                "establish": bool(text.get("establish", True)), # Default to true for MQTT updates
            }
            try:
                await self.send_json(safe)
            except Exception as e2:
                try:
                    print("⚠️ fallback send_json also failed:", e2, flush=True)
                except Exception:
                    pass