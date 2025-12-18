class GeminiError(Exception):
    """Errors talking to or interpreting responses from Gemini."""


class CommandParseError(Exception):
    """Gemini response could not be parsed into the expected JSON command."""


class UnknownCommandError(Exception):
    """The requested action is not supported by the voice agent."""


class CommandValidationError(Exception):
    """The command JSON is structurally invalid or missing required fields."""


class EntityNotFoundError(Exception):
    """Referenced home/room/lamp could not be resolved for this user."""


class AmbiguousEntityError(Exception):
    """A name resolved to multiple possible entities and could not be disambiguated."""


class DomainActionError(Exception):
    """
    Wrap domain-level errors (permissions, timeouts, etc.) so the view can
    map them into appropriate HTTP responses.
    """

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


