# Obsidian AI

AI-powered query interface for your Obsidian notes. Ask questions in natural language and get answers synthesized from your personal knowledge base.

## Features

- **Natural Language Queries**: Ask questions about your notes and get AI-generated answers
- **Multi-Provider LLM Support**: OpenAI, Anthropic Claude, Azure OpenAI, OpenRouter
- **Smart Model Routing**: Automatically routes simple queries to cheaper models and complex queries to more capable ones
- **Cost Tracking**: Real-time tracking of LLM costs with detailed breakdowns
- **Semantic Search**: Uses embeddings to find relevant notes
- **Incremental Sync**: Only re-indexes changed notes to save on embedding costs
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- At least one LLM API key (OpenAI, Anthropic, etc.)

### Local Development

1. **Clone and setup backend:**

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys and notes path

# Install dependencies
pip install -e ".[dev]"

# Run the backend
uvicorn app.main:app --reload
```

2. **Setup frontend:**

```bash
cd frontend
npm install
npm run dev
```

3. **Open http://localhost:5173**

4. **Build the index** by clicking the Database icon and running "Sync Now"

### Docker Deployment

1. **Configure environment:**

```bash
cp .env.example .env
# Edit root .env with your settings
# Required for notes access in containers:
# NOTES_HOST_PATH=/absolute/path/to/your/obsidian/vault
# Optional: customize container ports
# BACKEND_PORT=8050
# FRONTEND_PORT=5274
```

2. **Build and run:**

```bash
docker-compose up --build
```

3. **Access app and API:**
- Frontend: `http://localhost:${FRONTEND_PORT}` (default `http://localhost`)
- Backend API: `http://localhost:${BACKEND_PORT}/api/v1` (default `http://localhost:8050/api/v1`)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | API key for accessing the backend |
| `NOTES_HOST_PATH` | Yes (Docker) | Absolute host path to your Obsidian vault; bind-mounted to `/notes` in container |
| `NOTES_PATH` | Yes (Local backend) | Path to your Obsidian vault when running backend outside Docker (`backend/.env`) |
| `OPENAI_API_KEY` | * | OpenAI API key |
| `ANTHROPIC_API_KEY` | * | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | * | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | * | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | * | Azure OpenAI deployment name |
| `OPENROUTER_API_KEY` | * | OpenRouter API key |

\* At least one LLM provider must be configured

### Model Configuration

Configure which models to use for different query types:

```bash
# Simple queries (quick lookups)
SIMPLE_QUERY_PROVIDER=openai
SIMPLE_QUERY_MODEL=gpt-4o-mini

# Complex queries (analysis, synthesis)
COMPLEX_QUERY_PROVIDER=anthropic
COMPLEX_QUERY_MODEL=claude-3-5-sonnet-20241022

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│              React + TypeScript + Tailwind                  │
│                    (Port 5173 / 80)                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/SSE
┌─────────────────────────▼───────────────────────────────────┐
│                        Backend                              │
│              FastAPI + Pydantic v2 + Python 3.11            │
│                      (Port 8000)                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Query       │  │ Model       │  │ Cost                │  │
│  │ Service     │  │ Router      │  │ Tracker             │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────────────┘  │
│         │                │                                   │
│  ┌──────▼──────┐  ┌──────▼──────────────────────────────┐   │
│  │ Vector      │  │ LLM Providers                       │   │
│  │ Store       │  │ (OpenAI, Anthropic, Azure, Router)  │   │
│  │ (ChromaDB)  │  └─────────────────────────────────────┘   │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Query
- `POST /api/v1/query` - Execute a query
- `POST /api/v1/query/stream` - Stream a query response

### Notes
- `GET /api/v1/notes` - List notes
- `GET /api/v1/notes/folders` - List folders
- `GET /api/v1/notes/{path}` - Get a note

### Index
- `GET /api/v1/index/status` - Get index status
- `POST /api/v1/index/sync` - Incremental sync
- `POST /api/v1/index/rebuild` - Full rebuild

### Cost
- `GET /api/v1/cost/summary` - Get cost summary
- `GET /api/v1/cost/history` - Get cost history
- `GET /api/v1/cost/pricing` - Get pricing table

### Settings
- `GET /api/v1/settings/models` - Get available models
- `GET /api/v1/settings/providers` - Get provider status

## License

MIT
