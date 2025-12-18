from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from drf_spectacular.utils import extend_schema

from .services.context_builder import build_user_context
from .services.gemini_client import transcribe_and_parse
from .services.command_router import route_command
from .services import exceptions as exc
from .serializers import VoiceCommandInputSerializer


class VoiceCommandView(APIView):
    """
    Entry point for the voice agent.

    Accepts an audio file upload and uses Gemini to convert it into a
    structured intent, then routes it to existing domain logic.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=VoiceCommandInputSerializer,
        responses={200: None},
    )
    def post(self, request, *args, **kwargs):
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return Response(
                {"error": "missing_audio", "detail": "Field 'audio' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Basic size/type guardrails; adjust as needed.
        if audio_file.size == 0:
            return Response(
                {"error": "empty_audio", "detail": "Uploaded audio file is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mime_type = getattr(audio_file, "content_type", None) or "audio/wav"
        audio_bytes = audio_file.read()

        # Build small, user-specific context (homes, rooms, lamps).
        user_context = build_user_context(request.user)

        try:
            command_dict = transcribe_and_parse(audio_bytes, mime_type, user_context)

            # If Gemini explicitly returns an unknown/unsupported action,
            # treat it as a 400 without raising an exception.
            action = command_dict.get("action")
            if not action or action == "unknown":
                return Response(
                    {
                        "error": "unrecognized_command",
                        "detail": "Voice command did not match any supported action.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = route_command(request.user, command_dict)
        except exc.CommandParseError as e:
            return Response(
                {"error": "command_parse_error", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exc.UnknownCommandError as e:
            return Response(
                {"error": "unrecognized_command", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exc.CommandValidationError as e:
            return Response(
                {"error": "invalid_command", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exc.EntityNotFoundError as e:
            return Response(
                {"error": "entity_not_found", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exc.AmbiguousEntityError as e:
            return Response(
                {"error": "ambiguous_entity", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exc.DomainActionError as e:
            return Response(
                {"error": "domain_error", "detail": str(e)},
                status=e.status_code if hasattr(e, "status_code") else status.HTTP_400_BAD_REQUEST,
            )
        except exc.GeminiError as e:
            return Response(
                {"error": "gemini_error", "detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(result, status=status.HTTP_200_OK)


