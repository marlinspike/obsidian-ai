"""Index management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import ApiKeyDep, SettingsDep
from app.models.index import IndexStatus, SyncResult
from app.services.llm.factory import LLMProviderFactory
from app.services.search.sync import SyncService
from app.services.storage.index_db import IndexDatabase
from app.services.storage.vector_store import VectorStore

router = APIRouter()

# Global sync service
_sync_service: SyncService | None = None


def get_sync_service(settings: SettingsDep) -> SyncService:
    """Get or create sync service singleton."""
    global _sync_service
    if _sync_service is None:
        vector_store = VectorStore(settings.chroma_persist_path)
        index_db = IndexDatabase(settings.sqlite_path)
        llm_factory = LLMProviderFactory(settings)
        embedding_provider = llm_factory.get_embedding_provider()

        _sync_service = SyncService(
            notes_path=settings.notes_path,
            vector_store=vector_store,
            index_db=index_db,
            embedding_provider=embedding_provider,
            embedding_model=settings.embedding_model,
        )
    return _sync_service


SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]


@router.get("/status", response_model=IndexStatus)
async def get_index_status(
    _: ApiKeyDep,
    sync_service: SyncServiceDep,
) -> IndexStatus:
    """Get current index status.

    Returns:
        Status with counts of indexed, pending, and deleted notes
    """
    return sync_service.get_status()


@router.post("/sync", response_model=SyncResult)
async def incremental_sync(
    _: ApiKeyDep,
    sync_service: SyncServiceDep,
) -> SyncResult:
    """Perform incremental sync of changed notes.

    Only re-indexes notes that have been added, modified, or deleted
    since the last sync.

    Returns:
        Sync result with statistics
    """
    return await sync_service.incremental_sync()


@router.post("/rebuild", response_model=SyncResult)
async def full_rebuild(
    _: ApiKeyDep,
    sync_service: SyncServiceDep,
) -> SyncResult:
    """Perform full rebuild of the index.

    Clears all existing data and re-indexes all notes.
    Use this when changing embedding models or if the index is corrupted.

    Returns:
        Sync result with statistics
    """
    return await sync_service.full_rebuild()
