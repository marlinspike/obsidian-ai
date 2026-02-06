"""Index and sync-related Pydantic models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class NoteIndexEntry(BaseModel):
    """Tracks indexed state of a note."""

    path: str  # Relative path from notes root
    content_hash: str  # SHA256 of content (detect changes)
    last_indexed: datetime  # When it was last embedded
    last_modified: datetime  # File modification time
    chunk_count: int  # Number of chunks created
    embedding_model: str  # Model used for embeddings


class IndexStatus(BaseModel):
    """Overall index status."""

    total_notes: int
    indexed_notes: int
    pending_notes: int  # New or modified, need indexing
    deleted_notes: int  # Removed from filesystem
    last_full_sync: datetime | None
    last_incremental_sync: datetime | None


class SyncResult(BaseModel):
    """Result of a sync operation."""

    notes_added: int
    notes_updated: int
    notes_deleted: int
    chunks_created: int
    embedding_tokens_used: int
    embedding_cost: Decimal = Field(decimal_places=6)
    duration_seconds: float
