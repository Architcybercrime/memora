# Memora

Personal AI agent with layered long-term memory, voice input, and a streaming chat UI.

Inspired by `langchain-ai/memory-agent` but rebuilt as a production-shaped stack:

| Layer          | Tech                                                  |
|----------------|-------------------------------------------------------|
| Agent          | LangGraph (recall → model → tools loop)               |
| LLM            | OpenAI `gpt-4o` (Anthropic Claude swap via env)       |
| Embeddings     | OpenAI `text-embedding-3-small` (1536d)               |
| Short-term mem | Redis (rolling per-session conversation buffer)       |
| Long-term mem  | Postgres + pgvector (HNSW cosine index)               |
| Voice STT      | `faster-whisper` (local, free, industry-grade)        |
| API            | FastAPI + SSE streaming                               |
| UI             | Next.js 15 (App Router) + Tailwind + Lucide           |
| Deploy         | Docker Compose                                        |

## Architecture

```
┌──────────┐  SSE  ┌──────────────┐                ┌──────────────┐
│ Next.js  │ ────► │   FastAPI    │ ─── recall ──► │  pgvector    │
│  chat    │ ◄──── │  (LangGraph) │ ─── store  ──► │  (long-term) │
│ + voice  │       │              │                └──────────────┘
└──────────┘       │              │ ─── buffer ──► ┌──────────────┐
                   │              │ ◄── history ── │   Redis      │
                   └──────────────┘                │ (short-term) │
                          │                        └──────────────┘
                          ▼ transcribe
                   faster-whisper
```

Memory flow per turn:

1. `recall_node` — semantic search top-K long-term memories for the latest user message
2. `model_node` — call LLM with `[system(memories+time)] + history` and bound tools
3. If the LLM calls `save_memory` / `forget_memory`, the tool node runs and loops back
4. Final assistant message streams to the client; user + assistant turns are appended to Redis

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
# put your OPENAI_API_KEY in backend/.env
docker compose up --build
```

- UI:        http://localhost:3000
- API docs:  http://localhost:8000/docs

## Local dev

### Backend

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

You need Postgres (with the `pgvector` extension) and Redis running locally. The fastest path is:

```bash
docker compose up -d postgres redis
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## API

| Method | Path                          | Description                       |
|--------|-------------------------------|-----------------------------------|
| POST   | `/chat`                       | SSE-stream one turn               |
| DELETE | `/chat/{user_id}/{session_id}`| Clear short-term buffer           |
| POST   | `/voice/transcribe`           | Multipart audio → text            |
| GET    | `/memories/{user_id}`         | List long-term memories           |
| POST   | `/memories/{user_id}`         | Insert a memory                   |
| GET    | `/memories/{user_id}/search?q=…` | Semantic search                |
| DELETE | `/memories/{user_id}/{id}`    | Delete one memory                 |
| DELETE | `/memories/{user_id}`         | Wipe all memories                 |
| GET    | `/health`                     | Liveness                          |

## Notes

- pgvector uses HNSW + cosine distance for production-grade ANN.
- Whisper model loads lazily and is warmed in the background on startup.
- Sessions auto-expire from Redis after 7 days of inactivity.
- The agent saves **only atomic, durable facts** via a tool call — the prompt explicitly forbids saving trivia.
- Switch LLM provider by setting `LLM_PROVIDER=anthropic` and `LLM_MODEL=claude-3-5-sonnet-latest` in `backend/.env`.
