"""FastAPI dependency injection."""

from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings
from app.services.notes.loader import NotesLoader

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _normalize_origin(url: str | None) -> str | None:
    """Normalize a URL into origin format (scheme://host[:port])."""
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_trusted_frontend_request(request: Request, frontend_url: str) -> bool:
    """Allow browser requests from configured frontend origin without header."""
    trusted_origin = _normalize_origin(frontend_url)
    if not trusted_origin:
        return False

    origin = _normalize_origin(request.headers.get("origin"))
    if origin == trusted_origin:
        return True

    referer = _normalize_origin(request.headers.get("referer"))
    return referer == trusted_origin


async def verify_api_key(
    request: Request,
    api_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """Verify the API key from request header.

    Args:
        api_key: API key from X-API-Key header
        settings: Application settings

    Returns:
        The API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    expected_key = settings.api_key.get_secret_value()

    if api_key:
        if api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        return api_key

    if _is_trusted_frontend_request(request, settings.frontend_url):
        return expected_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing API key",
    )


_notes_loader: NotesLoader | None = None


def get_notes_loader(settings: Settings = Depends(get_settings)) -> NotesLoader:
    """Get the notes loader singleton.

    Args:
        settings: Application settings

    Returns:
        NotesLoader instance
    """
    global _notes_loader
    if _notes_loader is None:
        _notes_loader = NotesLoader(settings.notes_path)
    return _notes_loader


# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
ApiKeyDep = Annotated[str, Depends(verify_api_key)]
NotesLoaderDep = Annotated[NotesLoader, Depends(get_notes_loader)]
