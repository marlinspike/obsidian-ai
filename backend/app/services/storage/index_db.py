"""SQLite-backed index tracking database."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from app.models.index import NoteIndexEntry


class IndexDatabase:
    """SQLite database for tracking indexed notes."""

    def __init__(self, db_path: Path):
        """Initialize index database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS note_index (
                    path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    last_indexed TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    embedding_model TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

    def upsert(self, entry: NoteIndexEntry) -> None:
        """Insert or update an index entry.

        Args:
            entry: Index entry to upsert
        """
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO note_index
                (path, content_hash, last_indexed, last_modified, chunk_count, embedding_model)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.path,
                    entry.content_hash,
                    entry.last_indexed.isoformat(),
                    entry.last_modified.isoformat(),
                    entry.chunk_count,
                    entry.embedding_model,
                ),
            )

    def get(self, path: str) -> NoteIndexEntry | None:
        """Get an index entry by path.

        Args:
            path: Note path

        Returns:
            Index entry or None
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM note_index WHERE path = ?", (path,)
            ).fetchone()

            if not row:
                return None

            return NoteIndexEntry(
                path=row["path"],
                content_hash=row["content_hash"],
                last_indexed=datetime.fromisoformat(row["last_indexed"]),
                last_modified=datetime.fromisoformat(row["last_modified"]),
                chunk_count=row["chunk_count"],
                embedding_model=row["embedding_model"],
            )

    def exists(self, path: str) -> bool:
        """Check if a note is indexed.

        Args:
            path: Note path

        Returns:
            True if indexed
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM note_index WHERE path = ?", (path,)
            ).fetchone()
            return row is not None

    def get_all(self) -> dict[str, NoteIndexEntry]:
        """Get all index entries.

        Returns:
            Dictionary of path -> entry
        """
        entries: dict[str, NoteIndexEntry] = {}
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM note_index").fetchall()
            for row in rows:
                entry = NoteIndexEntry(
                    path=row["path"],
                    content_hash=row["content_hash"],
                    last_indexed=datetime.fromisoformat(row["last_indexed"]),
                    last_modified=datetime.fromisoformat(row["last_modified"]),
                    chunk_count=row["chunk_count"],
                    embedding_model=row["embedding_model"],
                )
                entries[entry.path] = entry
        return entries

    def delete(self, path: str) -> None:
        """Delete an index entry.

        Args:
            path: Note path to delete
        """
        with self._conn() as conn:
            conn.execute("DELETE FROM note_index WHERE path = ?", (path,))

    def clear(self) -> None:
        """Clear all index entries."""
        with self._conn() as conn:
            conn.execute("DELETE FROM note_index")
            conn.execute("DELETE FROM sync_metadata")

    def get_indexed_count(self) -> int:
        """Get count of indexed notes.

        Returns:
            Number of indexed notes
        """
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM note_index").fetchone()
            return row["count"] if row else 0

    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value.

        Args:
            key: Metadata key

        Returns:
            Value or None
        """
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM sync_metadata WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sync_metadata (key, value) VALUES (?, ?)",
                (key, value),
            )

    def get_last_full_sync(self) -> datetime | None:
        """Get timestamp of last full sync.

        Returns:
            Datetime or None
        """
        value = self.get_metadata("last_full_sync")
        return datetime.fromisoformat(value) if value else None

    def set_last_full_sync(self, timestamp: datetime) -> None:
        """Set timestamp of last full sync.

        Args:
            timestamp: Sync timestamp
        """
        self.set_metadata("last_full_sync", timestamp.isoformat())

    def get_last_incremental_sync(self) -> datetime | None:
        """Get timestamp of last incremental sync.

        Returns:
            Datetime or None
        """
        value = self.get_metadata("last_incremental_sync")
        return datetime.fromisoformat(value) if value else None

    def set_last_incremental_sync(self, timestamp: datetime) -> None:
        """Set timestamp of last incremental sync.

        Args:
            timestamp: Sync timestamp
        """
        self.set_metadata("last_incremental_sync", timestamp.isoformat())
