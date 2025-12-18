from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from Places_Lamp.models import Home, Room, Lamp
from VoiceAgent.services.command_router import route_command
from VoiceAgent.services import exceptions as exc


class CommandRouterTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pass")
        self.home = Home.objects.create(owner=self.user, name="Main Home")
        self.room = Room.objects.create(home=self.home, name="Living Room")
        self.lamp = Lamp.objects.create(room=self.room, name="Ceiling")

    def test_create_home(self):
        cmd = {"action": "create_home", "home_name": "New Home"}
        result = route_command(self.user, cmd)
        self.assertEqual(result["action"], "create_home")
        self.assertEqual(result["home"]["name"], "New Home")

    def test_set_lamp_status_uses_entities(self):
        cmd = {
            "action": "set_lamp_status",
            "home_name": "Main Home",
            "room_name": "Living Room",
            "lamp_name": "Ceiling",
            "status": "on",
        }
        # Mock MQTT helper so we don't depend on real device/MQTT timing.
        with patch(
            "Places_Lamp.services.lamp_control.set_lamp_status",
            return_value={
                "id": self.lamp.id,
                "name": self.lamp.name,
                "status": True,
                "room_id": self.room.id,
                "room_name": self.room.name,
                "home_id": self.home.id,
                "home_name": self.home.name,
            },
        ):
            result = route_command(self.user, cmd)
            self.assertEqual(result["action"], "set_lamp_status")
            self.assertEqual(result["lamp"]["name"], "Ceiling")

    def test_entity_not_found_raises(self):
        cmd = {
            "action": "set_lamp_status",
            "home_name": "Unknown Home",
            "room_name": "Living Room",
            "lamp_name": "Ceiling",
            "status": "on",
        }
        with self.assertRaises(exc.EntityNotFoundError):
            route_command(self.user, cmd)


class VoiceCommandViewTests(TestCase):
    """
    Tests for the VoiceCommandView with mocked Gemini + lamp control.
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="bob", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Basic fixtures for entity-related tests
        self.home = Home.objects.create(owner=self.user, name="Main Home")
        self.room = Room.objects.create(home=self.home, name="Living Room")
        self.lamp = Lamp.objects.create(room=self.room, name="Ceiling")

    def _fake_audio(self):
        return SimpleUploadedFile(
            "test.wav",
            b"fake-binary-audio",
            content_type="audio/wav",
        )

    def test_missing_audio_returns_400(self):
        url = reverse("voiceagent:voice-command")
        resp = self.client.post(url, {}, format="multipart")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "missing_audio")

    @patch("VoiceAgent.views.transcribe_and_parse")
    @patch("Places_Lamp.services.lamp_control.set_lamp_status")
    def test_successful_set_lamp_status_flow(self, mock_set_status, mock_parse):
        """
        Full happy path: audio → Gemini intent → router → lamp control.
        """
        url = reverse("voiceagent:voice-command")
        mock_parse.return_value = {
            "action": "set_lamp_status",
            "home_name": "Main Home",
            "room_name": "Living Room",
            "lamp_name": "Ceiling",
            "status": "on",
        }
        mock_set_status.return_value = {
            "id": self.lamp.id,
            "name": self.lamp.name,
            "status": True,
            "room_id": self.room.id,
            "room_name": self.room.name,
            "home_id": self.home.id,
            "home_name": self.home.name,
        }

        resp = self.client.post(
            url,
            {"audio": self._fake_audio()},
            format="multipart",
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["lamp"]["name"], "Ceiling")

    @patch("VoiceAgent.views.transcribe_and_parse")
    def test_unrecognized_command_returns_400(self, mock_parse):
        url = reverse("voiceagent:voice-command")
        mock_parse.side_effect = exc.UnknownCommandError("not supported")

        resp = self.client.post(
            url,
            {"audio": self._fake_audio()},
            format="multipart",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"], "unrecognized_command")

    @patch("VoiceAgent.views.transcribe_and_parse")
    def test_gemini_error_returns_502(self, mock_parse):
        url = reverse("voiceagent:voice-command")
        mock_parse.side_effect = exc.GeminiError("gemini down")

        resp = self.client.post(
            url,
            {"audio": self._fake_audio()},
            format="multipart",
        )

        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.data["error"], "gemini_error")

