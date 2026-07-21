# harness_and_loop_engineering

A learning project: building an AI agent **harness** from scratch, incrementally,
to understand agentic memory, loop engineering, and harness engineering by hand
(not with a framework). It's a tiny hand-rolled agent with a web UI where the
data-flow diagram lights up box-by-box as each step runs, so you can *watch* what
the agent does.

- **Chat model:** `deepseek-v4-flash` on [ollama.com](https://ollama.com) (cloud).
- **Embedding model:** `embeddinggemma` on a **local** Ollama daemon (Ollama cloud
  has no embedding model, so embeddings must run locally).
- **Web:** FastAPI + Server-Sent Events + one vanilla HTML page (no build step).

## What it does (Step 2: episodic memory + RAG)

The conversation is stored as **episodic memory** in a **Chroma vector store**.
Each user+assistant exchange is embedded and saved. On every new message the agent
builds a **hybrid context**: the top-k most relevant past exchanges (retrieved
across *all* chats) + the current chat's recent turns + your new message. That's
Retrieval-Augmented Generation (RAG). Memory survives a server restart.

There are **multiple chats**: a "New Chat" button and a sidebar of past chats.
Each chat's view shows only its own turns, but memory is **shared** — retrieval
searches across every chat.

## Prerequisites

- **Python** with [`uv`](https://docs.astral.sh/uv/) (the package manager this
  project uses).
- **[Ollama](https://ollama.com/download) installed and running locally** (it
  serves the embedding model at `http://localhost:11434`).
- An **Ollama cloud API key** for the chat model
  ([create one here](https://ollama.com/settings/keys)).

## Setup

```bash
# 1. Clone
git clone https://github.com/Saurav-Ganguly/harness_and_loop_engineering.git
cd harness_and_loop_engineering

# 2. Install dependencies (uv reads pyproject.toml / uv.lock)
uv sync

# 3. Pull the local embedding model (one time)
ollama pull embeddinggemma

# 4. Add your Ollama cloud key
cp .env.example .env        # then edit .env and paste your key
```

Your `.env` must contain:

```
ollama_key=your_ollama_cloud_key_here
```

`.env` is git-ignored — your key is never committed.

## Run

```bash
uv run uvicorn server:app --port 8000
```

Then open <http://localhost:8000> and start chatting. Try it: tell it a fact in
one chat, click **New Chat**, and ask about that fact — it still remembers,
because memory is shared across chats.

## Test

```bash
uv run pytest
```

Tests use fakes for the chat client and the store, so they need no network and no
Chroma.

## Files

| File | Role |
|------|------|
| `agent.py` | The harness: retrieve + recent → build context → call LLM → save the exchange. |
| `episodic.py` | The episodic memory vector store: `embed`, `add`, `retrieve` (top-k), `recent`, `all`, `sessions`. |
| `server.py` | FastAPI plumbing: cloud chat client + local embed client + store; endpoints `/chat`, `/history?session=`, `/sessions`. |
| `static/index.html` | Chat UI + chat-list sidebar + the live pipeline diagram. |
| `test_agent.py` | Agent tests (no network, no Chroma). |
| `docs/` | The step diagrams and scraped Ollama API docs. |

## Notes

- Memory lives in `memory/chroma/` (git-ignored). Delete that folder to start with
  a blank memory.
- Avoid `uvicorn --reload`: its child processes can be orphaned on interrupt and
  then hold port 8000 / lock the Chroma files. Use `--port 8000` without `--reload`.
