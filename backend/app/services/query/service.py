"""Query orchestration service."""

import time
from decimal import Decimal
from typing import AsyncIterator
from urllib.parse import quote

from app.config import Settings
from app.core.logging import logger
from app.models.query import (
    NoteReference,
    QueryComplexity,
    QueryRequest,
    QueryResponse,
    StreamChunk,
)
from app.services.cost.tracker import CostTracker
from app.services.llm.factory import LLMProviderFactory
from app.services.notes.loader import NotesLoader
from app.services.router.model_router import ModelRouter
from app.services.storage.vector_store import SearchResult, VectorStore


def build_obsidian_url(vault_path: str, note_path: str) -> str:
    """Build an Obsidian URL to open a note.

    Args:
        vault_path: Path to the Obsidian vault
        note_path: Relative path to the note within the vault

    Returns:
        Obsidian URL (obsidian://open?vault=...&file=...)
    """
    # Extract vault name from path (last directory component)
    vault_name = vault_path.rstrip("/").split("/")[-1]

    # Remove .md extension for Obsidian URL
    file_path = note_path
    if file_path.endswith(".md"):
        file_path = file_path[:-3]

    # URL encode the components
    return f"obsidian://open?vault={quote(vault_name)}&file={quote(file_path)}"


# System prompt for the LLM
SYSTEM_PROMPT = """You are an AI assistant that helps users query their personal notes stored in Obsidian.
You have access to relevant excerpts from the user's notes based on their question.

Guidelines:
1. Answer questions based primarily on the provided note excerpts
2. If the notes don't contain relevant information, say so clearly
3. Reference specific notes when citing information (use the note titles)
4. Be concise but thorough
5. If asked about people, meetings, or events, provide context from the notes
6. If you notice patterns or connections across notes, mention them
7. Always indicate which notes your answer is based on

The user's notes are provided below in the context section."""


def format_context(results: list[SearchResult]) -> str:
    """Format search results as context for the LLM.

    Args:
        results: Search results from vector store

    Returns:
        Formatted context string
    """
    if not results:
        return "No relevant notes found for this query."

    context_parts = ["=== Relevant Note Excerpts ===\n"]

    for i, result in enumerate(results, 1):
        header = f" (Section: {result.header_context})" if result.header_context else ""
        context_parts.append(
            f"[{i}] From: {result.note_path}{header}\n"
            f"---\n{result.content}\n---\n"
        )

    return "\n".join(context_parts)


class QueryService:
    """Orchestrates the query pipeline."""

    def __init__(
        self,
        settings: Settings,
        vector_store: VectorStore,
        notes_loader: NotesLoader,
        llm_factory: LLMProviderFactory,
        cost_tracker: CostTracker,
    ):
        """Initialize query service.

        Args:
            settings: Application settings
            vector_store: Vector store for search
            notes_loader: Notes loader for metadata
            llm_factory: LLM provider factory
            cost_tracker: Cost tracking service
        """
        self.settings = settings
        self.vector_store = vector_store
        self.notes_loader = notes_loader
        self.llm_factory = llm_factory
        self.cost_tracker = cost_tracker
        self.model_router = ModelRouter(settings, llm_factory)

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Execute a query and return the response.

        Args:
            request: Query request

        Returns:
            Query response with answer and metadata
        """
        start_time = time.time()

        # Route to appropriate model
        provider, complexity = self.model_router.route(
            request.question,
            request.complexity,
        )

        logger.info(
            f"Query routed to {provider.provider.value}/{provider.model} "
            f"(complexity: {complexity.value})"
        )

        # Get embedding provider for search
        embedding_provider = self.llm_factory.get_embedding_provider()

        # Embed the query
        query_embeddings, embed_tokens = await embedding_provider.embed([request.question])
        query_embedding = query_embeddings[0]

        # Search for relevant chunks
        # Get more results when filtering by folder to ensure we have enough after filtering
        search_limit = request.max_sources * 4 if request.folders else request.max_sources * 2
        results = self.vector_store.search(
            query_embedding,
            limit=search_limit,
        )

        # Filter by folders if specified (prefix matching to include subfolders)
        if request.folders:
            results = [
                r for r in results
                if any(
                    r.folder == folder or r.folder.startswith(folder + "/")
                    for folder in request.folders
                )
            ]

        # Limit to requested max
        results = results[: request.max_sources]

        # Format context for LLM
        context = format_context(results)

        # Build prompt
        prompt = f"""Context from your notes:

{context}

Question: {request.question}

Please answer based on the provided note excerpts. If the information isn't in the notes, say so."""

        # Get LLM response
        response = await provider.complete(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
        )

        # Calculate costs
        query_cost = self.cost_tracker.calculate_cost(
            model=provider.model,
            provider=provider.provider,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            embedding_tokens=embed_tokens,
        )

        # Build note references
        sources = self._build_references(results)

        latency_ms = int((time.time() - start_time) * 1000)

        return QueryResponse(
            answer=response.content,
            sources=sources,
            complexity_used=complexity,
            model_used=provider.model,
            provider_used=provider.provider.value,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            embedding_tokens=embed_tokens,
            total_cost=query_cost.total_cost,
            latency_ms=latency_ms,
        )

    async def stream_query(
        self, request: QueryRequest
    ) -> AsyncIterator[StreamChunk]:
        """Execute a query and stream the response.

        Args:
            request: Query request

        Yields:
            Stream chunks with content, sources, and metadata
        """
        start_time = time.time()

        # Route to appropriate model
        provider, complexity = self.model_router.route(
            request.question,
            request.complexity,
        )

        logger.info(
            f"Streaming query routed to {provider.provider.value}/{provider.model} "
            f"(complexity: {complexity.value})"
        )

        # Get embedding provider for search
        embedding_provider = self.llm_factory.get_embedding_provider()

        # Embed the query
        query_embeddings, embed_tokens = await embedding_provider.embed([request.question])
        query_embedding = query_embeddings[0]

        # Search for relevant chunks
        # Get more results when filtering by folder to ensure we have enough after filtering
        search_limit = request.max_sources * 4 if request.folders else request.max_sources * 2
        results = self.vector_store.search(
            query_embedding,
            limit=search_limit,
        )

        # Filter by folders if specified (prefix matching to include subfolders)
        if request.folders:
            results = [
                r for r in results
                if any(
                    r.folder == folder or r.folder.startswith(folder + "/")
                    for folder in request.folders
                )
            ]

        results = results[: request.max_sources]

        # Build and yield sources early
        sources = self._build_references(results)
        yield StreamChunk(type="sources", sources=sources)

        # Format context for LLM
        context = format_context(results)

        prompt = f"""Context from your notes:

{context}

Question: {request.question}

Please answer based on the provided note excerpts. If the information isn't in the notes, say so."""

        # Stream LLM response
        total_content = ""
        final_usage = None

        try:
            async for content, usage in provider.stream(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.7,
            ):
                if content:
                    total_content += content
                    yield StreamChunk(type="content", content=content)
                if usage:
                    final_usage = usage

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield StreamChunk(type="error", error=str(e))
            return

        # Calculate costs
        if final_usage:
            query_cost = self.cost_tracker.calculate_cost(
                model=provider.model,
                provider=provider.provider,
                input_tokens=final_usage.prompt_tokens,
                output_tokens=final_usage.completion_tokens,
                embedding_tokens=embed_tokens,
            )
            total_cost = query_cost.total_cost
        else:
            total_cost = Decimal("0")

        latency_ms = int((time.time() - start_time) * 1000)

        # Yield final metadata
        yield StreamChunk(
            type="metadata",
            metadata={
                "complexity_used": complexity.value,
                "model_used": provider.model,
                "provider_used": provider.provider.value,
                "input_tokens": final_usage.prompt_tokens if final_usage else 0,
                "output_tokens": final_usage.completion_tokens if final_usage else 0,
                "embedding_tokens": embed_tokens,
                "total_cost": str(total_cost),
                "latency_ms": latency_ms,
            },
        )

        yield StreamChunk(type="done")

    def _build_references(self, results: list[SearchResult]) -> list[NoteReference]:
        """Build note references from search results.

        Args:
            results: Search results

        Returns:
            List of note references
        """
        references: list[NoteReference] = []
        seen_paths: set[str] = set()

        for result in results:
            # Deduplicate by note path
            if result.note_path in seen_paths:
                continue
            seen_paths.add(result.note_path)

            # Get note title
            note = self.notes_loader.load_note(result.note_path)
            title = note.title if note else result.note_path

            # Build Obsidian URL
            obsidian_url = build_obsidian_url(
                str(self.settings.notes_path),
                result.note_path,
            )

            references.append(
                NoteReference(
                    note_path=result.note_path,
                    title=title,
                    relevant_excerpt=result.content[:300] + "..."
                    if len(result.content) > 300
                    else result.content,
                    folder=result.folder,
                    similarity_score=result.similarity,
                    obsidian_url=obsidian_url,
                )
            )

        return references
