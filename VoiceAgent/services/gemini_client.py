import base64
import json
from typing import Dict, Any

from urllib.parse import urlencode

import requests
from django.conf import settings

from . import exceptions as exc


def _build_prompt(user_context: Dict[str, Any]) -> str:
  """
  Build a system/user prompt that explains the SmartLight domain and
  provides a small, user-specific context of homes/rooms/lamps.
  """
  # Keep this text concise – it is sent on every request.
  intro = (
      "You are a smart home voice agent for a system called SmartLight. "
      "The user can create homes, rooms, lamps, and turn lamps on or off.\n\n"
      "You must ALWAYS respond with a single JSON object describing one action, "
      "with no additional text.\n"
      "Supported actions:\n"
      '- {\"action\": \"create_home\", \"home_name\": string}\n'
      '- {\"action\": \"create_room\", \"home_name\": string, \"room_name\": string}\n'
      '- {\"action\": \"create_lamp\", \"home_name\": string, \"room_name\": string, \"lamp_name\": string}\n'
      '- {\"action\": \"set_lamp_status\", \"home_name\": string, \"room_name\": string, \"lamp_name\": string, \"status\": \"on\" | \"off\"}\n\n'
      "User context (existing entities):\n"
  )

  ctx_json = json.dumps(user_context, ensure_ascii=False)
  instructions = (
      "\nUse the user context to choose existing home/room/lamp names when the "
      "user refers to them. If the user clearly wants to create something new, "
      "still fill the JSON fields with the requested names.\n\n"
      "Always respond ONLY with JSON, no natural language explanation.\n"
      "If the request does not match any supported action, respond with:\n"
      "{\"action\": \"unknown\"}\n"
  )

  return intro + ctx_json + instructions


def transcribe_and_parse(audio_bytes: bytes, mime_type: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
  """
  Call Google Gemini's generateContent endpoint to:
    1) Transcribe the audio.
    2) Interpret the transcript as a SmartLight command.
    3) Return a strict JSON intent parsed from the model's text response.

  This assumes:
    - settings.GEMINI_ENDPOINT points to a models/...:generateContent URL
    - settings.GEMINI_API_KEY is a Google API key.
  """
  endpoint = getattr(settings, "GEMINI_ENDPOINT", None)
  api_key = getattr(settings, "GEMINI_API_KEY", None)

  if not endpoint or not api_key:
      raise exc.GeminiError("Gemini integration is not configured (missing GEMINI_ENDPOINT or GEMINI_API_KEY).")

  # Build full URL with API key in query string, as per Google docs.
  url = f"{endpoint}?{urlencode({'key': api_key})}"

  prompt = _build_prompt(user_context)

  # Encode audio inline as base64 for Gemini's inline_data.
  audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

  body = {
      "contents": [
          {
              "role": "user",
              "parts": [
                  {"text": prompt},
                  {
                      "inline_data": {
                          "mime_type": mime_type or "audio/webm",
                          "data": audio_b64,
                      }
                  },
              ],
          }
      ],
  }

  headers = {
      "Content-Type": "application/json",
  }

  try:
      resp = requests.post(url, headers=headers, json=body, timeout=30)
  except requests.RequestException as e:
      raise exc.GeminiError(f"Failed to call Gemini endpoint: {e}")

  if resp.status_code >= 500:
      raise exc.GeminiError(f"Gemini service error: {resp.status_code}")

  try:
      payload = resp.json()
  except ValueError:
      raise exc.CommandParseError("Gemini response was not valid JSON.")

  # Lightweight debug logging – safe while developing.
  # Avoid logging secrets; this only logs model output and basic context.
  try:  # pragma: no cover - logging only
      print("[VoiceAgent] Gemini HTTP status:", resp.status_code, flush=True)
      print("[VoiceAgent] Gemini raw JSON response:", payload, flush=True)
  except Exception:
      pass

  # Extract the model's text response (Gemini generateContent format).
  try:
      candidates = payload.get("candidates") or []
      first = candidates[0] if candidates else {}
      content = first.get("content") or {}
      parts = content.get("parts") or []
      text = parts[0].get("text") if parts else None
  except Exception:
      text = None

  if not text or not isinstance(text, str):
      # As a fallback, if the whole payload already looks like a command dict,
      # try to use it directly.
      if isinstance(payload, dict) and "action" in payload:
          command = payload
      else:
          raise exc.CommandParseError("Gemini response did not contain a text part to parse.")
  else:
      # Model was instructed to return JSON as text; parse it.
      try:
          command = json.loads(text)
      except json.JSONDecodeError as e:
          raise exc.CommandParseError(f"Failed to parse Gemini text as JSON: {e}")

  if not isinstance(command, dict):
      raise exc.CommandParseError("Gemini response JSON was not an object.")

  # Normalize unknown action.
  action = command.get("action")
  try:  # pragma: no cover - logging only
      print("[VoiceAgent] Parsed Gemini command:", command, flush=True)
  except Exception:
      pass

  return command


