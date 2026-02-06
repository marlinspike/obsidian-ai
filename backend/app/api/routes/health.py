"""Health check endpoint."""

from pydantic import BaseModel
from fastapi import APIRouter

from app import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check if the API is healthy.

    Returns:
        Health status and version
    """
    return HealthResponse(status="healthy", version=__version__)
