"""API routes."""

from fastapi import APIRouter

from app.api.routes import cost, health, index, notes, query, settings

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(index.router, prefix="/index", tags=["index"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
