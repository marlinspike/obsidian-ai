"""Sync service for indexing notes."""

import hashlib
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.core.logging import logger
from app.models.cost import DEFAULT_PRICING
from app.models.index import IndexStatus, NoteIndexEntry, SyncResult
from app.models.note import NoteChunk
from app.services.llm.base import BaseLLMProvider
from app.services.notes.loader import NotesLoader
from app.services.notes.parser import NoteParser
from app.services.storage.index_db import IndexDatabase
from app.services.storage.vector_store import VectorStore


class SyncService:
    """Handles intelligent sync between filesystem and vector store."""

    # Batch size for embedding requests
    EMBEDDING_BATCH_SIZE = 100

    def __init__(
        self,
        notes_path: Path,
        vector_store: VectorStore,
        index_db: IndexDatabase,
        embedding_provider: BaseLLMProvider,
        embedding_model: str,
    ):
        """Initialize sync service.

        Args:
            notes_path: Path to notes directory
            vector_store: Vector store instance
            index_db: Index database instance
            embedding_provider: LLM provider for embeddings
            embedding_model: Model name for embeddings
        """
        self.notes_path = notes_path
        self.vector_store = vector_store
        self.index_db = index_db
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.loader = NotesLoader(notes_path)
        self.parser = NoteParser(notes_path)

    def get_status(self) -> IndexStatus:
        """Get current sync status.

        Returns:
            Index status with counts and timestamps
        """
        # Scan filesystem
        filesystem_notes = {
            str(p.relative_to(self.notes_path)): p for p in self.loader.scan_notes()
        }

        # Get indexed notes
        indexed_entries = self.index_db.get_all()

        # Detect pending (new or modified)
        pending_count = 0
        for note_path, file_path in filesystem_notes.items():
            entry = indexed_entries.get(note_path)
            if not entry:
                pending_count += 1  # New note
            else:
                current_hash = self._hash_file(file_path)
                if entry.content_hash != current_hash:
                    pending_count += 1  # Modified note

        # Detect deleted
        deleted_count = sum(
            1 for path in indexed_entries if path not in filesystem_notes
        )

        return IndexStatus(
            total_notes=len(filesystem_notes),
            indexed_notes=len(indexed_entries) - deleted_count,
            pending_notes=pending_count,
            deleted_notes=deleted_count,
            last_full_sync=self.index_db.get_last_full_sync(),
            last_incremental_sync=self.index_db.get_last_incremental_sync(),
        )

    async def incremental_sync(self) -> SyncResult:
        """Sync only changed notes.

        Returns:
            Sync result with statistics
        """
        start_time = time.time()
        result = SyncResult(
            notes_added=0,
            notes_updated=0,
            notes_deleted=0,
            chunks_created=0,
            embedding_tokens_used=0,
            embedding_cost=Decimal("0"),
            duration_seconds=0,
        )

        # Scan filesystem
        filesystem_notes = {
            str(p.relative_to(self.notes_path)): p for p in self.loader.scan_notes()
        }

        # Get indexed notes
        indexed_entries = self.index_db.get_all()

        # Find pending notes (new or modified)
        pending_notes: list[tuple[str, Path, bool]] = []  # (path, file_path, is_new)
        for note_path, file_path in filesystem_notes.items():
            entry = indexed_entries.get(note_path)
            if not entry:
                pending_notes.append((note_path, file_path, True))
            else:
                current_hash = self._hash_file(file_path)
                if entry.content_hash != current_hash:
                    pending_notes.append((note_path, file_path, False))

        # Find deleted notes
        deleted_notes = [path for path in indexed_entries if path not in filesystem_notes]

        # Process pending notes
        all_chunks: list[NoteChunk] = []
        chunk_metadata: list[tuple[str, int, str]] = []  # (path, chunk_count, hash)

        for note_path, file_path, is_new in pending_notes:
            try:
                note = self.parser.parse_file(file_path)
                chunks = self.parser.chunk_note(note)

                if not is_new:
                    # Delete old chunks from vector store
                    self.vector_store.delete_by_note(note_path)

                all_chunks.extend(chunks)
                chunk_metadata.append((note_path, len(chunks), self._hash_file(file_path)))

                if is_new:
                    result.notes_added += 1
                else:
                    result.notes_updated += 1

                logger.info(f"{'Added' if is_new else 'Updated'}: {note_path} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"Failed to process {note_path}: {e}")
                continue

        # Generate embeddings in batches
        if all_chunks:
            embeddings, tokens = await self._embed_chunks(all_chunks)
            result.embedding_tokens_used = tokens
            result.chunks_created = len(all_chunks)

            # Add to vector store
            self.vector_store.add_chunks(all_chunks, embeddings)

            # Update index database
            chunk_offset = 0
            for note_path, chunk_count, content_hash in chunk_metadata:
                file_path = filesystem_notes[note_path]
                self.index_db.upsert(
                    NoteIndexEntry(
                        path=note_path,
                        content_hash=content_hash,
                        last_indexed=datetime.utcnow(),
                        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                        chunk_count=chunk_count,
                        embedding_model=self.embedding_model,
                    )
                )
                chunk_offset += chunk_count

        # Handle deletions
        for deleted_path in deleted_notes:
            self.vector_store.delete_by_note(deleted_path)
            self.index_db.delete(deleted_path)
            result.notes_deleted += 1
            logger.info(f"Deleted: {deleted_path}")

        result.duration_seconds = time.time() - start_time
        result.embedding_cost = self._calculate_cost(result.embedding_tokens_used)

        self.index_db.set_last_incremental_sync(datetime.utcnow())

        logger.info(
            f"Incremental sync completed: "
            f"+{result.notes_added} ~{result.notes_updated} -{result.notes_deleted} notes, "
            f"{result.chunks_created} chunks, "
            f"${result.embedding_cost:.6f} cost, "
            f"{result.duration_seconds:.2f}s"
        )

        return result

    async def full_rebuild(self) -> SyncResult:
        """Complete rebuild of index.

        Returns:
            Sync result with statistics
        """
        start_time = time.time()
        result = SyncResult(
            notes_added=0,
            notes_updated=0,
            notes_deleted=0,
            chunks_created=0,
            embedding_tokens_used=0,
            embedding_cost=Decimal("0"),
            duration_seconds=0,
        )

        # Clear everything
        self.vector_store.clear()
        self.index_db.clear()

        # Process all notes
        all_chunks: list[NoteChunk] = []
        chunk_metadata: list[tuple[str, int, str, Path]] = []

        for file_path in self.loader.scan_notes():
            note_path = str(file_path.relative_to(self.notes_path))
            try:
                note = self.parser.parse_file(file_path)
                chunks = self.parser.chunk_note(note)

                all_chunks.extend(chunks)
                chunk_metadata.append(
                    (note_path, len(chunks), self._hash_file(file_path), file_path)
                )
                result.notes_added += 1

                logger.debug(f"Processed: {note_path} ({len(chunks)} chunks)")

            except Exception as e:
                logger.error(f"Failed to process {note_path}: {e}")
                continue

        # Generate embeddings in batches
        if all_chunks:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            embeddings, tokens = await self._embed_chunks(all_chunks)
            result.embedding_tokens_used = tokens
            result.chunks_created = len(all_chunks)

            # Add to vector store
            logger.info("Adding chunks to vector store...")
            self.vector_store.add_chunks(all_chunks, embeddings)

            # Update index database
            for note_path, chunk_count, content_hash, file_path in chunk_metadata:
                self.index_db.upsert(
                    NoteIndexEntry(
                        path=note_path,
                        content_hash=content_hash,
                        last_indexed=datetime.utcnow(),
                        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
                        chunk_count=chunk_count,
                        embedding_model=self.embedding_model,
                    )
                )

        result.duration_seconds = time.time() - start_time
        result.embedding_cost = self._calculate_cost(result.embedding_tokens_used)

        self.index_db.set_last_full_sync(datetime.utcnow())

        logger.info(
            f"Full rebuild completed: "
            f"{result.notes_added} notes, "
            f"{result.chunks_created} chunks, "
            f"${result.embedding_cost:.6f} cost, "
            f"{result.duration_seconds:.2f}s"
        )

        return result

    async def _embed_chunks(
        self, chunks: list[NoteChunk]
    ) -> tuple[list[list[float]], int]:
        """Generate embeddings for chunks in batches.

        Args:
            chunks: List of chunks to embed

        Returns:
            Tuple of (embeddings, total_tokens)
        """
        all_embeddings: list[list[float]] = []
        total_tokens = 0

        # Process in batches
        for i in range(0, len(chunks), self.EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + self.EMBEDDING_BATCH_SIZE]
            texts = [c.content for c in batch]

            embeddings, tokens = await self.embedding_provider.embed(texts)
            all_embeddings.extend(embeddings)
            total_tokens += tokens

            logger.debug(f"Embedded batch {i // self.EMBEDDING_BATCH_SIZE + 1}: {len(batch)} chunks")

        return all_embeddings, total_tokens

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of hash
        """
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def _calculate_cost(self, tokens: int) -> Decimal:
        """Calculate embedding cost.

        Args:
            tokens: Number of tokens used

        Returns:
            Cost in dollars
        """
        pricing = DEFAULT_PRICING.get(self.embedding_model)
        if not pricing or not pricing.embedding_price_per_million:
            return Decimal("0")

        cost = (Decimal(tokens) / Decimal("1000000")) * pricing.embedding_price_per_million
        return cost.quantize(Decimal("0.000001"))
