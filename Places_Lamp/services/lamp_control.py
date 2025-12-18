import time

import paho.mqtt.publish as publish
from django.conf import settings

from Places_Lamp.models import Lamp
from VoiceAgent.services import exceptions as exc


def set_lamp_status(*, user, lamp: Lamp, desired_status: bool):
    """
    Core MQTT + DB polling logic extracted from the REST view so it can be
    reused by the voice agent.
    """
    if not lamp.can_access(user):
        raise exc.DomainActionError(
            "Not allowed to control this lamp.", status_code=403
        )

    payload = "ON" if desired_status else "OFF"
    topic = f"Devices/{lamp.token}/command"

    try:
        publish.single(
            topic, payload, hostname=settings.MQTT_BROKER, port=settings.MQTT_PORT
        )
        print(f"MQTT PUB → {user.username} → {topic}={payload}", flush=True)
    except Exception as e:  # pragma: no cover - network failure path
        raise exc.DomainActionError(
            f"Lamp status updated locally but MQTT publish failed: {e}",
            status_code=200,
        )

    deadline = time.time() + 5.0

    while time.time() < deadline:
        time.sleep(0.5)
        refreshed = Lamp.objects.get(pk=lamp.pk)
        if bool(refreshed.status) == bool(desired_status):
            return {
                "id": refreshed.id,
                "name": refreshed.name,
                "status": bool(refreshed.status),
                "room_id": refreshed.room.id,
                "room_name": refreshed.room.name,
                "home_id": refreshed.room.home.id,
                "home_name": refreshed.room.home.name,
            }

    current = Lamp.objects.get(pk=lamp.pk)
    raise exc.DomainActionError(
        "Lamp status command timed out without device confirmation.", status_code=504
    )


