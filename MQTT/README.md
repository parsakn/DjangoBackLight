## MQTT Message Contract (Backend ↔ Devices)

This backend speaks MQTT on two topics per lamp, using the lamp’s `token` UUID.

- Command topic (backend → device): `Devices/<token>/command`
- Status topic (device → backend): `Devices/<token>/status`

### Commands (backend → device)
- **Topic:** `Devices/<token>/command`
- **Payload (plain text):**
  - `"ON"` – turn lamp on
  - `"OFF"` – turn lamp off
  - `"DEL"` – (optional) deletion/cleanup command

Notes:
- Payloads are *plain strings* (no JSON envelope).
- The backend normalizes booleans/1/0/“on”/“off” to `ON`/`OFF` before publishing.

### Status updates (device → backend)
- **Topic:** `Devices/<token>/status`
- **Payload (JSON object):**
  ```json
  {
    "msg": "1",            // required; "1"/"ON" -> on, "0"/"OFF" -> off
    "establish": "Connected" // optional; when present and == "Connected", marks lamp.connection = True
  }
  ```
- Backend interpretation:
  - `"msg"`: `"1"`, `"on"`, `"ON"` ⇒ status = True; `"0"`, `"off"`, `"OFF"` ⇒ status = False.
  - `"establish": "Connected"`: sets `Lamp.connection = True` and notifies subscribers.
- If payload isn’t valid JSON, the bridge logs a warning and drops to channel forwarding.

### Backend behavior on incoming status
- Parses `token` from topic (`Devices/<token>/status`).
- Updates `Lamp.status` (and `Lamp.connection` when `establish` is provided).
- Broadcasts updates to:
  - Home owner
  - Users in `lamp.shared_with`
  - Users in `home.shared_with`
- Also forwards the raw message into the Channels layer (`mqtt` channel) for `MqttConsumer`.

### Publish flow (backend)
- REST `PATCH /lamp/{id}/status/` → publishes `ON`/`OFF` on `Devices/<token>/command`.
- WebSocket `LightConsumer` → publishes `ON`/`OFF` (or `DEL`) on `Devices/<token>/command`.
- All publishing is plain text; no `{"msg": ...}` envelope is used anymore.

### Subscribe flow (backend)
- `mqtt_bridge` subscribes to `Devices/+/status` and feeds:
  - Direct DB updates for status/connection.
  - Channel message `{"type": "mqtt.sub", "text": {"topic": "...", "payload": <json or None>}}` to `MqttConsumer`.

### Quick examples
- Turn on (backend → device):
  - Topic: `Devices/550e8400-e29b-41d4-a716-446655440000/command`
  - Payload: `ON`
- Device reports on:
  - Topic: `Devices/550e8400-e29b-41d4-a716-446655440000/status`
  - Payload: `{"msg": "1"}`
- Device signals it connected:
  - Payload: `{"msg": "1", "establish": "Connected"}`

