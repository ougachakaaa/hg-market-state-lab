"""Publication failures are transport independent and never silently repaired."""


class PublicationError(Exception):
    category = "publication_error"


class InvalidPublicationInput(PublicationError):
    category = "invalid_input"


class PublicationNotFound(PublicationError):
    category = "not_found"


class PublicationCorrupt(PublicationError):
    category = "corrupt"


class UnsupportedPublicationVersion(PublicationError):
    category = "unsupported_version"


class InconsistentPublication(PublicationError):
    category = "inconsistent"


class PublicationUnavailable(PublicationError):
    category = "unavailable"


class PublicationCollision(PublicationError):
    category = "collision"
