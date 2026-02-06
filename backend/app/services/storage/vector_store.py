"""ChromaDB vector store for semantic search."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models.note import NoteChunk


class SearchResult:
    """Result from a vector search."""

    def __init__(
        self,
        note_path: str,
        content: str,
        header_context: str,
        folder: str,
        distance: float,
    ):
        self.note_path = note_path
        self.content = content
        self.header_context = header_context
        self.folder = folder
        self.distance = distance
        # Convert distance to similarity (cosine distance -> similarity)
        self.similarity = 1 - distance


class VectorStore:
    """ChromaDB-backed vector store with persistence."""

    COLLECTION_NAME = "obsidian_notes"
    # ChromaDB max batch size (leave some headroom)
    MAX_BATCH_SIZE = 5000

    def __init__(self, persist_path: Path):
        """Initialize vector store with persistence.

        Args:
            persist_path: Directory to persist ChromaDB data
        """
        persist_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[NoteChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Add chunks with embeddings to the store.

        Handles batching to stay within ChromaDB limits.

        Args:
            chunks: List of note chunks
            embeddings: Corresponding embeddings
        """
        if not chunks:
            return

        # Process in batches to avoid ChromaDB batch size limit
        for i in range(0, len(chunks), self.MAX_BATCH_SIZE):
            batch_chunks = chunks[i:i + self.MAX_BATCH_SIZE]
            batch_embeddings = embeddings[i:i + self.MAX_BATCH_SIZE]

            self.collection.add(
                ids=[f"{c.note_path}:{c.chunk_index}" for c in batch_chunks],
                embeddings=batch_embeddings,
                documents=[c.content for c in batch_chunks],
                metadatas=[
                    {
                        "note_path": c.note_path,
                        "chunk_index": c.chunk_index,
                        "header_context": c.header_context,
                        "folder": c.folder,
                    }
                    for c in batch_chunks
                ],
            )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        folder_filter: str | None = None,
    ) -> list[SearchResult]:
        """Search for similar chunks.

        Args:
            query_embedding: Query vector
            limit: Maximum results to return
            folder_filter: Optional folder to filter by

        Returns:
            List of search results ordered by similarity
        """
        where: dict[str, Any] | None = None
        if folder_filter:
            where = {"folder": folder_filter}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []

        if results["documents"] and results["metadatas"] and results["distances"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, dists):
                search_results.append(
                    SearchResult(
                        note_path=str(meta.get("note_path", "")),
                        content=doc or "",
                        header_context=str(meta.get("header_context", "")),
                        folder=str(meta.get("folder", "")),
                        distance=float(dist),
                    )
                )

        return search_results

    def delete_by_note(self, note_path: str) -> None:
        """Delete all chunks for a note.

        Args:
            note_path: Path of the note to delete
        """
        self.collection.delete(where={"note_path": note_path})

    def get_chunk_count(self) -> int:
        """Get total number of chunks in the store.

        Returns:
            Number of chunks
        """
        return self.collection.count()

    def clear(self) -> None:
        """Clear all data and recreate collection."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def get_notes_in_store(self) -> set[str]:
        """Get all unique note paths currently in the store.

        Returns:
            Set of note paths
        """
        # Get all metadata
        result = self.collection.get(include=["metadatas"])
        if not result["metadatas"]:
            return set()

        return {str(m.get("note_path", "")) for m in result["metadatas"] if m}
