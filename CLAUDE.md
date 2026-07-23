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

**Step 2 (done) — the memory system** (see [step-2.png](docs/step-2.png)).
Three memory types feed working memory: **episodic** (Chroma vector store of
timestamped chat history), **semantic** (flat JSON file of durable facts + user
profile, injected whole every turn), **procedural** (skill.md files — how to act).
After N turns a cheaper summarizer agent distills episodes into semantic facts. Built
in increments, each validated before moving on:

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
     (increment 3) resolves.
3. **Semantic + summarizer (done)** — semantic memory is a **flat JSON file**
   (`memory/facts.json`), not a vector store: the fact set is small and always
   relevant, so ALL facts are injected as a system block every turn. A cheaper cloud
   model (`gemma4:cloud`) consolidates: every N total episodes (and on New Chat) it
   reads all episodes + current facts and REWRITES the reconciled fact set, collapsing
   contradictions. Ollama Cloud ignores structured outputs, so it parses
   one-fact-per-line text.
4. **Procedural (done)** — skills live at `memory/procedural_memory/<name>/skill.md`
   (name + description trigger + body procedure). Selection is retrieval again: each
   skill's **description** is embedded once (cached in a Chroma `procedural`
   collection, new skills only), the incoming message is embedded, and the nearest
   skill wins **only if** it clears a distance threshold (1.15, calibrated). Top-1;
   no match = no skill. The matched body is injected as its own system block. The UI's
   Procedural Memory box shows the match (or nearest near-miss) + distance.

Deferred improvements are tracked in [docs/memory-backlog.md](docs/memory-backlog.md)
(headlined by incremental/watermarked consolidation). **Next: loop engineering.**

## Tech / model

- **Chat model: Ollama cloud** (`https://ollama.com`) via the `ollama` library. Model: `deepseek-v4-flash`.
- **Embedding model: local Ollama** (`http://localhost:11434`, no key). Model: `embeddinggemma`
  (`ollama pull embeddinggemma`). Ollama cloud has **no** embedding model, so embeddings must run locally.
- **Summarizer model: Ollama cloud** (`gemma4:cloud`) — distills episodes into facts.
- **Vector store: Chroma** (`chromadb`), persisted at `memory/chroma/` — collections
  `episodes` (episodic) and `procedural` (skill description embeddings).
- **Semantic facts:** flat JSON at `memory/facts.json`. **Procedural skills:**
  `memory/procedural_memory/<name>/skill.md`. Both under `memory/`, but the skills are
  version-controlled (source) while the vector store + facts stay git-ignored (local).
- Auth key is in `.env` as `ollama_key` (see `.env.example`). `.env` is git-ignored.
  **NEVER read `.env`.** Ask Saurav for any value needed.
- Web: FastAPI + Server-Sent Events + a single vanilla HTML page (no build step).
- Python managed with `uv` (`uv run ...`, `uv add ...`) per global rules.

## Source files

- [agent.py](agent.py) — the harness: retrieves episodes, loads facts, selects a skill,
  assembles context, calls the LLM, saves the exchange, consolidates every N turns,
  yields a stage event per step. Knows nothing about the web.
- [episodic.py](episodic.py) — the episodic memory vector store: embed via local Ollama,
  `add` / `retrieve` (top-k) / `recent` / `all` / `count` / `sessions`, backed by Chroma.
- [semantic.py](semantic.py) — semantic memory: a flat JSON list of durable facts,
  `all` / `replace`. No embeddings — injected whole every turn.
- [summarizer.py](summarizer.py) — the summarizer agent: `consolidate(episodes, facts)`
  distills + reconciles into a new fact set via the cheap cloud model.
- [procedural.py](procedural.py) — procedural memory: loads `skill.md` bodies from disk,
  caches description embeddings in Chroma, `select(message)` returns the matched skill or
  none by a distance threshold.
- [server.py](server.py) — FastAPI plumbing: builds the cloud chat client + local embed
  client + all stores, serves the page, streams events as SSE, exposes `/history`,
  `/sessions`, `/facts`, `/consolidate`.
- [static/index.html](static/index.html) — chat UI + the pipeline diagram + facts panel.
- [test_agent.py](test_agent.py), [test_semantic.py](test_semantic.py),
  [test_summarizer.py](test_summarizer.py) — tests (no network; use fakes/tmp files).

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
