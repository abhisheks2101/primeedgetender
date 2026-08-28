"""Structured collection errors."""

from dataclasses import dataclass

from app.core.enums import CollectionErrorType


@dataclass(slots=True)
class CollectionError(Exception):
    error_type: CollectionErrorType
    message: str
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class NetworkCollectionError(CollectionError):
    def __init__(self, message: str = "Network error during collection.") -> None:
        super().__init__(CollectionErrorType.NETWORK, message, retryable=True)


class TimeoutCollectionError(CollectionError):
    def __init__(self, message: str = "Request timed out during collection.") -> None:
        super().__init__(CollectionErrorType.TIMEOUT, message, retryable=True)


class HttpCollectionError(CollectionError):
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(CollectionErrorType.HTTP, message, retryable=retryable)


class ParsingCollectionError(CollectionError):
    def __init__(self, message: str = "Failed to parse source response.") -> None:
        super().__init__(CollectionErrorType.PARSING, message, retryable=False)


class ValidationCollectionError(CollectionError):
    def __init__(self, message: str = "Collected data failed validation.") -> None:
        super().__init__(CollectionErrorType.VALIDATION, message, retryable=False)


class SourceUnavailableError(CollectionError):
    def __init__(self, message: str = "Tender source is unavailable.") -> None:
        super().__init__(CollectionErrorType.SOURCE_UNAVAILABLE, message, retryable=True)


class UnexpectedCollectionError(CollectionError):
    def __init__(self, message: str = "Unexpected collection error.") -> None:
        super().__init__(CollectionErrorType.UNEXPECTED, message, retryable=False)
