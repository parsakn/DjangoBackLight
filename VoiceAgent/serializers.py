from rest_framework import serializers


class VoiceCommandInputSerializer(serializers.Serializer):
    """
    Simple serializer used only for API schema so that Swagger/Redoc
    display a proper file upload field for the voice command endpoint.
    """

    audio = serializers.FileField(help_text="Audio file containing the voice command.")


