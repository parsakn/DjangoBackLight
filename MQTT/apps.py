from django.apps import AppConfig
import sys
import threading




class MqttConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MQTT'
    def ready(self):
        # Auto-start MQTT bridge only for the development runserver command.
        # Avoid starting during manage.py migrate, test, shell, collectstatic, etc.
        try:
            argv = sys.argv
        except Exception:
            argv = []

        if len(argv) >= 2 and argv[1] in ("runserver",):
            # Start in a daemon thread so it doesn't block process exit.
            from .mqtt_bridge import start_bridge

            def _start():
                try:
                    start_bridge()
                except Exception:
                    pass

            t = threading.Thread(target=_start, daemon=True)
            t.start()

