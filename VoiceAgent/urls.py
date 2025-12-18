from django.urls import path
from .views import VoiceCommandView

app_name = "voiceagent"

urlpatterns = [
    path("command/", VoiceCommandView.as_view(), name="voice-command"),
]


