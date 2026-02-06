"""Query endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.api.deps import ApiKeyDep, SettingsDep
from app.config import Settings, get_settings
from app.models.query import QueryRequest, QueryResponse
from app.services.cost.tracker import CostTracker
from app.services.llm.factory import LLMProviderFactory
from app.services.notes.loader import NotesLoader
from app.services.query.service import QueryService
from app.services.storage.index_db import IndexDatabase
from app.services.storage.vector_store import VectorStore

router = APIRouter()

# Global services (initialized on first request)
_query_service: QueryService | None = None
_cost_tracker: CostTracker | None = None
_settings_cache: Settings | None = None


def get_cost_tracker(settings: Settings = Depends(get_settings)) -> CostTracker:
    """Get or create cost tracker singleton with persistence."""
    global _cost_tracker, _settings_cache
    if _cost_tracker is None:
        _settings_cache = settings
        _cost_tracker = CostTracker(
            persist_path=settings.costs_path,
            auto_save=True,
        )
    return _cost_tracker


def get_query_service(settings: SettingsDep) -> QueryService:
    """Get or create query service singleton."""
    global _query_service
    if _query_service is None:
        cost_tracker = get_cost_tracker(settings)
        vector_store = VectorStore(settings.chroma_persist_path)
        notes_loader = NotesLoader(settings.notes_path)
        llm_factory = LLMProviderFactory(settings)

        _query_service = QueryService(
            settings=settings,
            vector_store=vector_store,
            notes_loader=notes_loader,
            llm_factory=llm_factory,
            cost_tracker=cost_tracker,
        )
    return _query_service


QueryServiceDep = Annotated[QueryService, Depends(get_query_service)]
CostTrackerDep = Annotated[CostTracker, Depends(get_cost_tracker)]


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    _: ApiKeyDep,
    service: QueryServiceDep,
) -> QueryResponse:
    """Execute a query against your notes.

    Args:
        request: Query request with question and options

    Returns:
        Query response with answer, sources, and cost info
    """
    return await service.query(request)


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    _: ApiKeyDep,
    service: QueryServiceDep,
) -> EventSourceResponse:
    """Stream a query response via Server-Sent Events.

    Args:
        request: Query request with question and options

    Returns:
        SSE stream with content chunks, sources, and metadata
    """

    async def event_generator():
        async for chunk in service.stream_query(request):
            yield {
                "event": chunk.type,
                "data": json.dumps(chunk.model_dump(exclude_none=True)),
            }

    return EventSourceResponse(event_generator())
