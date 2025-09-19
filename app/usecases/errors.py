"""Usecase-level domain exceptions for routing and error mapping."""


class UsecaseError(Exception):
    """Base exception for usecase errors."""


class NotFoundError(UsecaseError):
    """Base for not-found errors."""


class VendorNotFoundError(NotFoundError):
    """Vendor entity not found or invalid."""


class FolderNotFoundError(NotFoundError):
    """Folder entity not found or invalid."""


class MessageNotFoundError(NotFoundError):
    """Message entity not found or mismatched ownership."""


class PartNotFoundError(NotFoundError):
    """Message part not found for given message."""


class ContentNotAvailableError(NotFoundError):
    """The part exists but has no binary content available."""


class ValidationError(UsecaseError):
    """Usecase validation error (bad input/state)."""


class ConflictError(UsecaseError):
    """Usecase conflict error (duplicate or state conflict)."""


class PlainTextRequiredError(UsecaseError):
    """The operation requires a text/plain body but it was not found."""
