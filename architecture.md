# Obsidian AI Architecture

## Purpose
Obsidian AI is a local-first RAG application for querying an Obsidian vault with LLMs. It provides:
- Semantic retrieval over markdown notes
- Model routing for cost/performance tradeoffs
- Streaming answers with source attribution
- Incremental indexing and cost tracking

## System Topology
```
Browser (React/Vite)
  -> /api/v1/* (HTTP + SSE)
FastAPI backend
  -> Notes filesystem (read .md vault)
  -> SQLite index metadata (note hash + sync metadata)
  -> ChromaDB vector store (chunk embeddings)
  -> LLM providers (OpenAI, Azure OpenAI, Anthropic, OpenRouter)
```

## Repository Map
- `frontend/`: React + TypeScript UI
- `backend/app/main.py`: FastAPI app factory, CORS, exception wiring
- `backend/app/api/routes/*`: API surface
- `backend/app/services/*`: core business logic
- `backend/app/models/*`: shared Pydantic contracts
- `backend/data/`: runtime persistence (`index.db`, Chroma data, `costs.json`)
- `docker-compose.yml`: local production topology

## Backend Architecture

### API Layer
- Mounted under `/api/v1` in `backend/app/main.py`.
- Auth is API-key based via `X-API-Key` in `backend/app/api/deps.py`, with trusted browser-origin bypass for the configured frontend origin.
- Routes:
- `health`: service liveness/version
- `query`: standard + SSE query endpoints
- `notes`: list notes/folders and fetch note content
- `index`: incremental sync and full rebuild
- `cost`: session/all-time cost reporting and resets
- `settings`: provider/model availability and current config

### Service Layer
- Query orchestration: `backend/app/services/query/service.py`
- Model routing: `backend/app/services/router/*`
- Note loading/parsing/chunking: `backend/app/services/notes/*`
- Sync/index orchestration: `backend/app/services/search/sync.py`
- Storage adapters: `backend/app/services/storage/*`
- LLM provider abstraction/factory: `backend/app/services/llm/*`
- Cost accounting/persistence: `backend/app/services/cost/tracker.py`

### Storage Model
- Vector store: Chroma persistent collection `obsidian_notes`.
- Index DB (SQLite):
- `note_index`: per-note content hash, chunk count, embedding model, timestamps.
- `sync_metadata`: `last_full_sync`, `last_incremental_sync`.
- Cost store: JSON file (`costs.json`) with query history and all-time aggregates.

### Provider Abstraction
- `BaseLLMProvider` contract:
- `complete(prompt, ...)`
- `stream(prompt, ...)`
- `embed(texts)`
- Implementations:
- `OpenAIProvider`
- `AzureOpenAIProvider`
- `AnthropicProvider` (no embeddings)
- `OpenRouterProvider`
- `LLMProviderFactory` creates/caches provider instances keyed by `provider:model`.

## Frontend Architecture

### App Composition
- Bootstrapped in `frontend/src/main.tsx` with:
- React Query client
- Theme provider
- `App` shell
- `App.tsx` controls:
- Query submission and streaming state
- Modal surfaces (Index, Cost, Settings)
- Session status footer

### Data Access
- Central client: `frontend/src/services/api.ts`.
- Axios for normal JSON requests.
- `fetch` + manual SSE parsing for streaming query endpoint.
- Type contracts in `frontend/src/types/index.ts` mirror backend schemas.

### UI Modules
- Query composition: `QueryInput`, `FolderSelector`
- Response rendering: `ResultsPanel`, `Markdown`
- Operations: `IndexStatus`, `CostDashboard`, `SettingsPanel`
- Theme: `ThemeToggle`, `useTheme`

## Core Runtime Flows

### 1) Query Flow (Streaming)
1. UI submits `QueryRequest` (`question`, `complexity`, optional folder filters).
2. Backend routes model via heuristic complexity analyzer.
3. Embedding provider embeds question.
4. Vector store returns top chunks; optional folder filtering is applied.
5. Prompt is built from chunk context + system instructions.
6. Chosen LLM streams response chunks.
7. Backend emits SSE chunks (`sources`, `content`, `metadata`, `done`).
8. Frontend incrementally renders answer and metadata.

### 2) Incremental Sync Flow
1. Scan vault markdown files (skipping system dirs/hidden/empty files).
2. Compare current file hashes to SQLite `note_index`.
3. Parse changed/new notes and chunk them.
4. Embed chunks in batches.
5. Upsert embeddings in Chroma.
6. Upsert note index rows and sync metadata in SQLite.
7. Delete removed notes from Chroma + SQLite.

### 3) Cost Tracking Flow
1. Query token usage is returned by provider adapters.
2. Cost tracker prices tokens using `DEFAULT_PRICING`.
3. Session totals and breakdowns are updated.
4. Data is auto-saved to `costs.json` when enabled.
5. All-time aggregates are served by `/cost/all-time`.

## Configuration and Environment

### Required Runtime Inputs
- `API_KEY`
- `NOTES_PATH` (local backend runs)
- `NOTES_HOST_PATH` (Docker bind mount source -> container `/notes`)
- At least one provider credential

### Routing/Model Inputs
- `SIMPLE_QUERY_PROVIDER`, `SIMPLE_QUERY_MODEL`
- `COMPLEX_QUERY_PROVIDER`, `COMPLEX_QUERY_MODEL`
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`

### Persistence Paths
- `CHROMA_PERSIST_PATH`
- `SQLITE_PATH`
- `COSTS_PATH` (backend setting defaults to `./data/costs.json`)

## Guiding Principles
- Clear contracts first: backend Pydantic models and frontend TS interfaces stay aligned.
- Keep provider logic isolated behind `BaseLLMProvider`.
- Separate orchestration from adapters:
- `QueryService`/`SyncService` orchestrate
- provider/storage classes adapt external systems
- Optimize incremental work:
- hash-based sync, batched embeddings, selective reindex
- Favor observability over hidden behavior:
- explicit route-level models, sync/cost summaries, logs
- Preserve local ownership:
- note data lives on local filesystem and local persisted stores

## Extension Playbook

### Add a New LLM Provider
1. Add enum value in `backend/app/models/llm.py`.
2. Implement provider class in `backend/app/services/llm/`.
3. Register construction path in `LLMProviderFactory`.
4. Add provider status + models in `backend/app/api/routes/settings.py`.
5. Add pricing entries in `backend/app/models/cost.py`.
6. Update frontend `LLMProvider` union in `frontend/src/types/index.ts`.

### Add a New Backend Capability
1. Create/extend a service in `backend/app/services/`.
2. Define request/response models in `backend/app/models/`.
3. Add route in `backend/app/api/routes/` and register in `routes/__init__.py`.
4. Add client function in `frontend/src/services/api.ts`.
5. Add/extend UI module in `frontend/src/components/`.

### Extend Retrieval Quality
1. Change chunking logic in `NoteParser.chunk_note`.
2. Add metadata-aware filtering/scoring in `VectorStore.search` and query orchestration.
3. Update source shaping in `QueryService._build_references`.
4. Validate sync behavior and index rebuild compatibility.

## Operational Notes
- Local dev:
- backend on `:8000`
- frontend on `:5173` (proxy `/api` to backend)
- Docker:
- nginx serves frontend on `:80`
- proxies `/api` to backend container
- SSE is explicitly configured in nginx (`proxy_buffering off`, long read timeout).

## Security Boundaries
- API key auth gates non-health endpoints for non-frontend-origin callers.
- CORS allowlist is single-origin from `FRONTEND_URL`.
- Vault is mounted read-only in Docker compose.

## Current Constraints and Technical Debt
- `get_settings()` comment says cached, but currently instantiates settings each call.
- Route-level global singletons (`_query_service`, `_sync_service`, `_cost_tracker`) are process-local and can drift from runtime config changes.
- Query-time embedding cost attribution uses the chat model's pricing record; this may undercount embedding spend unless model pricing includes embedding rates.
- `SettingsPanel` styling is not fully theme-token based like the rest of the UI.
- No backend/frontend automated tests are currently present.

## Recommended Engineering Guardrails for Future Extensions
- Add contract tests for API schemas (backend models <-> frontend types).
- Add provider conformance tests for `complete/stream/embed`.
- Add sync regression fixtures for complex note formats.
- Add e2e smoke test for streaming query + source rendering + cost updates.
- Keep new features behind service interfaces, not route handlers.
