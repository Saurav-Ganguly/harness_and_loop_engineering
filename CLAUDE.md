# Building a Harness

Learning project: build an agentic system from scratch, incrementally, following a
YouTube teacher's system design. Order of learning: **agentic memory system design
→ loop engineering → harness engineering.** We implement it step by step, validating
each increment before moving on.

## Goal

Understand and build the pieces of an AI agent harness by hand — not use a framework.
Small steps, working code at each stage.

Repo: https://github.com/Saurav-Ganguly/harness_and_loop_engineering

## Current stage

**Step 1 (done)** — the basic ephemeral agent session (see [step-1.png](docs/step-1.png)):
`system prompt + chat history + user prompt` → assembled into working memory (context)
→ LLM → reply, with a web UI whose pipeline boxes light up as each step runs.
History is a plain in-memory list on the server (the single source of truth); the
browser rebuilds it on load via `GET /history`. Nothing survives a server restart yet.

**Step 2 (in progress) — the memory system** (see [step-2.png](docs/step-2.png)).
Three memory types feed working memory: **procedural** (skill/.md files — how to act),
**semantic** (vector store of durable facts + user profile), **episodic** (vector store
of timestamped chat history). After N chats a cheaper summarizer agent distills episodes
into semantic facts. We build it in increments, validating each before moving on:

1. **Persistence + episodic (done)** — turns saved to disk so memory survives a
   restart. (Started as a JSON file; increment 2 replaced it with the vector store.)
2. **Retrieval (RAG) (done)** — episodic memory is a **Chroma vector store**. Each
   user+assistant pair is embedded and saved; context is a **hybrid** of the top-k
   relevant pairs (retrieved across ALL chats) + the current chat's recent turns +
   the new message. Embeddings run on a **local Ollama** daemon (`embeddinggemma`);
   the chat model stays on cloud.
   - **Multi-chat (done)** — each episode is tagged with a `session_id`. The UI has
     a **New Chat** button and a sidebar of past chats; a chat's view shows only its
     own turns, but retrieval is **shared** across every chat. Endpoints: `/sessions`,
     `/history?session=<id>`, and `/chat` takes `session_id`. This is what lets two
     chats hold contradicting facts (red vs blue Tesla) - which the summarizer
     (increment 3) will resolve.
3. **Semantic + summarizer (next)** — after N turns a cheaper model distills episodes
   into durable facts; retrieved by RAG.
4. **Procedural** — load `.md` skill files into the system prompt (how to act).

## Tech / model

- **Chat model: Ollama cloud** (`https://ollama.com`) via the `ollama` library. Model: `deepseek-v4-flash`.
- **Embedding model: local Ollama** (`http://localhost:11434`, no key). Model: `embeddinggemma`
  (`ollama pull embeddinggemma`). Ollama cloud has **no** embedding model, so embeddings must run locally.
- **Vector store: Chroma** (`chromadb`), persisted at `memory/chroma/`.
- Auth key is in `.env` as `ollama_key` (see `.env.example`). `.env` is git-ignored.
  **NEVER read `.env`.** Ask Saurav for any value needed.
- Web: FastAPI + Server-Sent Events + a single vanilla HTML page (no build step).
- Python managed with `uv` (`uv run ...`, `uv add ...`) per global rules.

## Source files

- [agent.py](agent.py) — the harness: retrieves from the store, assembles context,
  calls the LLM, saves the exchange, yields a stage event per step. Knows nothing about the web.
- [episodic.py](episodic.py) — the episodic memory vector store: embed via local Ollama,
  `add` / `retrieve` (top-k) / `all`, backed by Chroma.
- [server.py](server.py) — FastAPI plumbing: builds the cloud chat client + local embed
  client + store, serves the page, streams events as SSE, exposes `GET /history`.
- [static/index.html](static/index.html) — chat UI + the pipeline diagram.
- [test_agent.py](test_agent.py) — agent tests (no network; uses a fake client).

## Reference

- [docs/step-1.png](docs/step-1.png) — the Step 1 diagram.
- [docs/step-2.png](docs/step-2.png) — the Step 2 (memory system) diagram.
- [docs/ollama_docs.md](docs/ollama_docs.md) — scraped Ollama API docs. Grep this
  instead of re-scraping.
- Global skill `ollama-api` — quick reference for Ollama API patterns.

## Run

- Prereq: local Ollama running with the embedding model: `ollama pull embeddinggemma`.
- Start: `uv run uvicorn server:app --port 8000` → open http://localhost:8000
- Test: `uv run pytest` (no network / no Chroma — uses fakes).
- Note: `--reload` spawns child processes; if a run is interrupted, orphaned children
  can hold port 8000 and lock `memory/chroma`. Kill stray `uvicorn server:app` PIDs.

## Working style

- Simple, incremental, no overengineering. Validate each step.
- Prove root cause before fixing bugs.
- Latest library APIs.
