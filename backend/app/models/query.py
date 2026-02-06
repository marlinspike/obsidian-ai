"""Query-related Pydantic models."""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class QueryComplexity(str, Enum):
    """Query complexity level for model routing."""

    SIMPLE = "simple"  # Quick lookup, single fact
    COMPLEX = "complex"  # Multi-step reasoning, synthesis
    AUTO = "auto"  # Let the system decide


class NoteReference(BaseModel):
    """Reference to a specific note section in a query response."""

    note_path: str
    title: str
    relevant_excerpt: str
    folder: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    obsidian_url: str | None = None  # obsidian://open URL to open in Obsidian


class QueryRequest(BaseModel):
    """Incoming query from user."""

    question: str = Field(min_length=1, max_length=5000)
    complexity: QueryComplexity = QueryComplexity.AUTO  # User can override
    folders: list[str] | None = None  # Filter to specific folders
    max_sources: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    """Response to a query."""

    answer: str
    sources: list[NoteReference]
    complexity_used: QueryComplexity
    model_used: str
    provider_used: str
    input_tokens: int
    output_tokens: int
    embedding_tokens: int
    total_cost: Decimal
    latency_ms: int


class StreamChunk(BaseModel):
    """A chunk of streamed response."""

    type: str  # "content", "sources", "metadata", "done", "error"
    content: str | None = None
    sources: list[NoteReference] | None = None
    metadata: dict[str, str | int | float] | None = None
    error: str | None = None
