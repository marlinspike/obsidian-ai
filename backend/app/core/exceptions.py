"""Custom exceptions for the application."""


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, code="NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class LLMError(AppError):
    """Raised when an LLM operation fails."""

    def __init__(self, provider: str, message: str):
        full_message = f"LLM error ({provider}): {message}"
        super().__init__(full_message, code="LLM_ERROR")
        self.provider = provider


class SyncError(AppError):
    """Raised when a sync operation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="SYNC_ERROR")


class ProviderNotConfiguredError(AppError):
    """Raised when trying to use a provider that isn't configured."""

    def __init__(self, provider: str):
        message = f"Provider not configured: {provider}. Please set the API key in .env"
        super().__init__(message, code="PROVIDER_NOT_CONFIGURED")
        self.provider = provider
