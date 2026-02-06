"""Note-related Pydantic models."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ObsidianNote(BaseModel):
    """Represents a parsed Obsidian note."""

    path: str  # Relative path from notes root
    title: str
    content: str
    headers: list[str] = Field(default_factory=list)  # Extracted headers (H1, H2, etc.)
    links: list[str] = Field(default_factory=list)  # [[wiki-style]] links
    tags: list[str] = Field(default_factory=list)  # #tags
    dates: list[date] = Field(default_factory=list)  # Extracted dates
    people: list[str] = Field(default_factory=list)  # Extracted people mentions
    folder: str  # Parent folder (Microsoft, Personal, etc.)
    last_modified: datetime
    frontmatter: dict[str, str | list[str] | None] = Field(default_factory=dict)


class NoteChunk(BaseModel):
    """A chunk of a note for embedding/retrieval."""

    note_path: str  # Relative path from notes root
    chunk_index: int  # Position within the note
    content: str
    header_context: str  # Which section this belongs to (e.g., "## Meeting Notes")
    folder: str  # Parent folder for filtering
