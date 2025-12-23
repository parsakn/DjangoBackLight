from typing import Dict, Any

from django.db.models import Q

from Places_Lamp.models import Home, Room, Lamp
from Places_Lamp.serializer import (
    HomePostSerializer,
    RoomPostSerializer,
    LampPostSerializer,
)
from . import exceptions as exc


SUPPORTED_ACTIONS = {
    "create_home",
    "create_room",
    "create_lamp",
    "set_lamp_status",
}


def _normalize_status(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"on", "true", "1"}:
            return True
        if v in {"off", "false", "0"}:
            return False
    raise exc.CommandValidationError("Invalid status value; expected 'on' or 'off'.")


def _find_home(user, home_name: str) -> Home:
    qs = Home.objects.filter(
        Q(owner=user, name__iexact=home_name)
        | Q(shared_with=user, name__iexact=home_name)
    ).distinct()
    count = qs.count()
    if count == 0:
        raise exc.EntityNotFoundError(f"Home '{home_name}' not found for this user.")
    if count > 1:
        raise exc.AmbiguousEntityError(f"Home name '{home_name}' is ambiguous.")
    return qs.first()


def _find_room(home: Home, room_name: str) -> Room:
    qs = Room.objects.filter(home=home, name__iexact=room_name)
    count = qs.count()
    if count == 0:
        raise exc.EntityNotFoundError(f"Room '{room_name}' not found in home '{home.name}'.")
    if count > 1:
        raise exc.AmbiguousEntityError(
            f"Room name '{room_name}' is ambiguous in home '{home.name}'."
        )
    return qs.first()


def _find_lamp(room: Room, lamp_name: str) -> Lamp:
    qs = Lamp.objects.filter(room=room, name__iexact=lamp_name)
    count = qs.count()
    if count == 0:
        raise exc.EntityNotFoundError(
            f"Lamp '{lamp_name}' not found in room '{room.name}'."
        )
    if count > 1:
        raise exc.AmbiguousEntityError(
            f"Lamp name '{lamp_name}' is ambiguous in room '{room.name}'."
        )
    return qs.first()


def handle_create_home(user, command: Dict[str, Any]) -> Dict[str, Any]:
    home_name = command.get("home_name")
    if not home_name:
        raise exc.CommandValidationError("Field 'home_name' is required for create_home.")

    serializer = HomePostSerializer(
        data={"name": home_name},
        context={"request": type("R", (), {"user": user})()},
    )
    serializer.is_valid(raise_exception=True)
    home = serializer.save(owner=user)
    return {"action": "create_home", "home": {"id": home.id, "name": home.name}}


def handle_create_room(user, command: Dict[str, Any]) -> Dict[str, Any]:
    home_name = command.get("home_name")
    room_name = command.get("room_name")
    if not home_name or not room_name:
        raise exc.CommandValidationError(
            "Fields 'home_name' and 'room_name' are required for create_room."
        )

    home = _find_home(user, home_name)
    serializer = RoomPostSerializer(
        data={"name": room_name, "home": home.id},
        context={"request": type("R", (), {"user": user})()},
    )
    serializer.is_valid(raise_exception=True)
    room = serializer.save()
    return {
        "action": "create_room",
        "room": {"id": room.id, "name": room.name, "home_id": home.id, "home_name": home.name},
    }


def handle_create_lamp(user, command: Dict[str, Any]) -> Dict[str, Any]:
    home_name = command.get("home_name")
    room_name = command.get("room_name")
    lamp_name = command.get("lamp_name")
    if not home_name or not room_name or not lamp_name:
        raise exc.CommandValidationError(
            "Fields 'home_name', 'room_name', and 'lamp_name' are required for create_lamp."
        )

    home = _find_home(user, home_name)
    room = _find_room(home, room_name)

    serializer = LampPostSerializer(
        data={"name": lamp_name, "room": room.id, "status": False},
        context={"request": type("R", (), {"user": user})()},
    )
    serializer.is_valid(raise_exception=True)
    lamp = serializer.save()

    return {
        "action": "create_lamp",
        "lamp": {
            "id": lamp.id,
            "name": lamp.name,
            "room_id": room.id,
            "room_name": room.name,
            "home_id": home.id,
            "home_name": home.name,
        },
    }


def handle_set_lamp_status(user, command: Dict[str, Any]) -> Dict[str, Any]:
    from Places_Lamp.services.lamp_control import set_lamp_status  # lazy import to avoid cycles

    home_name = command.get("home_name")
    room_name = command.get("room_name")
    lamp_name = command.get("lamp_name")
    raw_status = command.get("status")

    if not home_name or not room_name or not lamp_name:
        raise exc.CommandValidationError(
            "Fields 'home_name', 'room_name', and 'lamp_name' are required for set_lamp_status."
        )

    if raw_status is None:
        raise exc.CommandValidationError("Field 'status' is required for set_lamp_status.")

    status_bool = _normalize_status(raw_status)

    home = _find_home(user, home_name)
    room = _find_room(home, room_name)
    lamp = _find_lamp(room, lamp_name)

    result = set_lamp_status(user=user, lamp=lamp, desired_status=status_bool)
    return {
        "action": "set_lamp_status",
        "lamp": result,
    }


def route_command(user, command: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the command structure and dispatch to the appropriate handler.
    """
    if not isinstance(command, dict):
        raise exc.CommandValidationError("Command must be a JSON object.")

    action = command.get("action")
    if not action or action not in SUPPORTED_ACTIONS:
        raise exc.UnknownCommandError(f"Unsupported action '{action}'.")

    if action == "create_home":
        return handle_create_home(user, command)
    if action == "create_room":
        return handle_create_room(user, command)
    if action == "create_lamp":
        return handle_create_lamp(user, command)
    if action == "set_lamp_status":
        return handle_set_lamp_status(user, command)

    # Fallback, should not be reached due to SUPPORTED_ACTIONS check.
    raise exc.UnknownCommandError(f"Unsupported action '{action}'.")


