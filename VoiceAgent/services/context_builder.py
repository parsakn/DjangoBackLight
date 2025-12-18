from typing import Dict, List

from Places_Lamp.models import Home, Room, Lamp


MAX_HOMES = 20
MAX_ROOMS = 50
MAX_LAMPS = 100


def _serialize_homes(homes) -> List[Dict]:
    return [{"name": h.name} for h in homes]


def _serialize_rooms(rooms) -> List[Dict]:
    return [{"home_name": r.home.name, "room_name": r.name} for r in rooms]


def _serialize_lamps(lamps) -> List[Dict]:
    return [
        {
            "home_name": l.room.home.name,
            "room_name": l.room.name,
            "lamp_name": l.name,
        }
        for l in lamps
    ]


def build_user_context(user) -> Dict:
    """
    Build a compact description of the user's homes, rooms and lamps
    that can be safely passed to Gemini as part of the prompt.
    """
    if not user.is_authenticated:
        return {"homes": [], "rooms": [], "lamps": []}

    # Homes owned by the user or shared with them.
    homes_qs = (
        Home.objects.filter(owner=user)
        | Home.objects.filter(shared_with=user)
    ).distinct()[:MAX_HOMES]

    # Rooms within those homes.
    rooms_qs = Room.objects.filter(home__in=homes_qs).distinct()[:MAX_ROOMS]

    # Lamps the user can see (owned via home/room or shared).
    lamps_qs = (
        Lamp.objects.filter(room__home__in=homes_qs)
        | Lamp.objects.filter(shared_with=user)
    ).distinct()[:MAX_LAMPS]

    return {
        "homes": _serialize_homes(homes_qs),
        "rooms": _serialize_rooms(rooms_qs),
        "lamps": _serialize_lamps(lamps_qs),
    }


