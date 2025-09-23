from django.apps import AppConfig
import sys
import threading
import os




class MqttConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MQTT'


    def ready(self):
        # Require an explicit opt-in to autostart the bridge during runserver.
        # This avoids surprising behavior where the bridge starts in the same
        # process (and possibly before ChannelNameRouter/consumers are ready)
        # which can make debugging cross-process delivery hard.
        if os.environ.get("MQTT_AUTOSTART", "false").lower() != "true":
            return

        # Avoid starting twice when runserver reloads
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .mqtt_bridge import start_bridge  # wherever your start_bridge lives

        def _run():
            try:
                start_bridge()
            except Exception as e:
                import traceback
                print("❌ MQTT bridge crashed:", e)
                traceback.print_exc()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        print("✅ MQTT bridge thread started")