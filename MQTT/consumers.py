from channels.consumer import SyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import async_to_sync
from asgiref.sync import sync_to_async
import paho.mqtt.publish as publish
from Places_Lamp.models import Lamp
from django.conf import settings
from django.contrib.auth import get_user_model
import json
from channels.layers import get_channel_layer

BROKER_URL = settings.MQTT_BROKER


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
        # User id may be passed at top-level 'user' or nested in text as 'user_id' depending on sender
        user_id = event.get("user") or (event.get("text") or {}).get("user_id") or (event.get("text") or {}).get("user")
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

        # Normalise payload so that devices always receive plain text "ON"/"OFF"
        # (or "DEL" for deletion) instead of a JSON envelope.
        if isinstance(payload, bool):
            normalized = "ON" if payload else "OFF"
        elif isinstance(payload, (int, float)):
            normalized = "ON" if int(payload) == 1 else "OFF"
        elif isinstance(payload, str):
            p = payload.strip().upper()
            if p in ("1", "ON"):
                normalized = "ON"
            elif p in ("0", "OFF"):
                normalized = "OFF"
            else:
                normalized = payload
        else:
            # Fallback: just cast to string
            normalized = str(payload)

        topic = f"Devices/{token}/command"

        # Special case: deletion command should be passed through as-is.
        if isinstance(normalized, str) and normalized.strip().upper() == "DEL":
            payload_to_send = "DEL"
        else:
            payload_to_send = normalized

        print(f"MQTT PUB → {user.username} → {topic}={payload_to_send}", flush=True)

        try:
            publish.single(topic, payload_to_send, hostname=BROKER_URL)
            print(f"MQTT publish succeeded for topic {topic} payload={payload_to_send}", flush=True)
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
        print("LightConsumer.connect: user =", getattr(user, "username", None), "auth=", getattr(user, "is_authenticated", False), flush=True)
        if user.is_authenticated:
            self.user_group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            await self.accept()
            
            # CRITICAL ADDITION: Re-synchronize state upon connection/reconnection
            await self.send_initial_lamp_status()
            
        else:
            print("LightConsumer.connect: anonymous user, closing connection", flush=True)
            await self.close()

    async def disconnect(self, code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)

    async def receive_json(self, content):
        # ... (Keep receive_json logic mostly as is, but ensure lamp.connection is passed in the broadcast)
        token = content.get("token")
        payload = content.get("payload") 
        user = self.scope.get("user")
        if payload == "DEL":
            # Option A: send to MQTT to notify device
            channel_layer = get_channel_layer()
            # send to mqtt channel with top-level user id for mqtt_pub resolver
            # use await since we're in async context
            await channel_layer.send(
                "mqtt",
                {
                    "type": "mqtt.pub",
                    "user": getattr(user, 'id', None),
                    "text": {"token": str(token), "payload": "DEL"},
                },
            )
            # Best-effort direct publish in case the named-channel consumer
            # isn't available (multi-process channel-layer issues). This
            # ensures the device sees the DEL command even if the other
            # process doesn't pick up the 'mqtt' channel message.
            try:
                topic = f"Devices/{token}/command"
                # publish.single is blocking; run it in a thread via sync_to_async
                await sync_to_async(publish.single)(topic, "DEL", hostname=BROKER_URL)
                print(f"Direct DEL publish succeeded for topic {topic}", flush=True)
            except Exception as e:
                print("⚠️ Direct DEL publish failed:", e, flush=True)
            # Optionally: delete the lamp in DB (after notifying device) or mark removed
            # lamp.delete()
            # or lamp.delete() only after device confirms
            # Broadcast to other users that lamp was deleted:
            # Broadcast deletion to all authorized users of this lamp
            # Gather targets and lamp metadata in a sync function to avoid
            # accessing Django ORM relations from the async event loop.
            def _gather_targets(tkn):
                l = Lamp.objects.select_related('room__home').get(token=tkn)
                owner = l.room.home.owner
                shared_ids = list(l.shared_with.values_list('id', flat=True))
                home_shared_ids = list(l.room.home.shared_with.values_list('id', flat=True))
                return {
                    'owner_id': owner.id,
                    'shared_ids': shared_ids,
                    'home_shared_ids': home_shared_ids,
                    'lamp_name': l.name,
                }

            try:
                info = await sync_to_async(_gather_targets)(token)
            except Exception:
                # If lamp cannot be found, at least notify the requester
                await self.channel_layer.group_send(
                    f"user_{getattr(user,'id',None)}",
                    {"type": "lamp.status", "text": {"token": str(token), "status": False, "deleted": True}},
                )
                return

            target_ids = [info['owner_id']] + info['shared_ids'] + info['home_shared_ids']
            # de-duplicate ids
            target_ids = list(dict.fromkeys(target_ids))

            for uid in target_ids:
                await self.channel_layer.group_send(
                    f"user_{uid}",
                    {"type": "lamp.status", "text": {"token": str(token), "status": False, "deleted": True}},
                )
            # Immediately delete the lamp from the database (destructive)
            try:
                await sync_to_async(Lamp.objects.filter(token=token).delete)()
                print(f"Lamp with token {token} deleted from DB by user {user.username}", flush=True)
            except Exception as e:
                print("⚠️ Failed to delete lamp from DB:", e, flush=True)
            return
        
        
         # e.g., "ON" / "OFF"
        
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
            parsed = LightConsumer.parse_bool(payload)

            # All ORM access happens inside this synchronous helper.
            def _prepare_and_update(tkn, usr, new_status):
                try:
                    l = Lamp.objects.select_related('room__home').get(token=tkn)
                except Lamp.DoesNotExist:
                    return None

                if not l.can_access(usr):
                    return None

                if new_status is not None:
                    l.__class__.objects.filter(pk=l.pk).update(status=new_status)

                owner = l.room.home.owner
                shared_ids = list(l.shared_with.values_list('id', flat=True))
                home_shared_ids = list(l.room.home.shared_with.values_list('id', flat=True))

                return {
                    'lamp_name': l.name,
                    'token': str(l.token),
                    'status': bool(new_status) if new_status is not None else bool(l.status),
                    'raw': payload,
                    'establish': l.connection,
                    'owner_id': owner.id,
                    'shared_ids': shared_ids,
                    'home_shared_ids': home_shared_ids,
                }

            info = await sync_to_async(_prepare_and_update)(token, user, parsed)
            if not info:
                return

            target_ids = [info['owner_id']] + info['shared_ids'] + info['home_shared_ids']
            target_ids = list(dict.fromkeys(target_ids))

            data = {
                'lamp': info['lamp_name'],
                'token': info['token'],
                'status': info['status'],
                'raw': info['raw'],
                'establish': info['establish'],
            }

            for uid in target_ids:
                await self.channel_layer.group_send(f"user_{uid}", {"type": "lamp.status", "text": data})

            # Fallback MQTT PUB logic (run in thread) with plain text payload.
            try:
                topic = f"Devices/{token}/command"
                # Reuse the same normalisation rules as mqtt_pub above.
                if isinstance(payload, bool):
                    fb_payload = "ON" if payload else "OFF"
                elif isinstance(payload, (int, float)):
                    fb_payload = "ON" if int(payload) == 1 else "OFF"
                elif isinstance(payload, str):
                    p2 = payload.strip().upper()
                    if p2 in ("1", "ON"):
                        fb_payload = "ON"
                    elif p2 in ("0", "OFF"):
                        fb_payload = "OFF"
                    else:
                        fb_payload = payload
                else:
                    fb_payload = str(payload)

                await sync_to_async(publish.single)(topic, fb_payload, hostname=BROKER_URL)
                print(f"Fallback MQTT PUB → {topic}={fb_payload}", flush=True)
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