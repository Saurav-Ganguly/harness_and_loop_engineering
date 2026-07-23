# harness_and_loop_engineering

A learning project: building an AI agent **harness** from scratch, incrementally,
to understand agentic memory, loop engineering, and harness engineering by hand
(not with a framework). It's a tiny hand-rolled agent with a web UI where the
data-flow diagram lights up box-by-box as each step runs, so you can *watch* what
the agent does.

- **Chat model:** `deepseek-v4-flash` on [ollama.com](https://ollama.com) (cloud).
- **Summarizer model:** `gemma4:cloud` (the cheaper model that distills facts).
- **Embedding model:** `embeddinggemma` on a **local** Ollama daemon (Ollama cloud
  has no embedding model, so embeddings must run locally).
- **Web:** FastAPI + Server-Sent Events + one vanilla HTML page (no build step).

## What it does (Step 2: the memory system)

Three memory types feed the agent's working memory (context) on every turn:

- **Episodic** — the conversation, stored in a **Chroma vector store**. Each
  user+assistant exchange is embedded and saved. Each message builds a **hybrid
  context**: the top-k most relevant past exchanges (retrieved across *all* chats) +
  the current chat's recent turns + your new message. That's RAG. There are **multiple
  chats** (a "New Chat" button + a sidebar); each chat's view shows only its own turns,
  but memory is **shared** — retrieval searches across every chat.
- **Semantic** — durable facts about you (a flat `memory/facts.json`), injected whole
  every turn. A cheaper model (`gemma4:cloud`) **consolidates** every N turns: it reads
  the episodes and rewrites a reconciled fact set, collapsing contradictions (say a red
  Tesla, later a blue one → one current fact).
- **Procedural** — reusable **skills** (`memory/procedural_memory/<name>/skill.md`) that
  tell the agent *how* to do a task. Each message is matched against the skills by
  embedding similarity; if one clears a threshold, its procedure is injected. Ships with
  `prompt_enhancer`, `idea_rater`, `idea_enhancer`.

Memory survives a server restart. The pipeline diagram lights up each memory step as it
runs, and the Procedural box shows which skill matched (or the nearest near-miss).

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
| `agent.py` | The harness: retrieve + facts + skill → build context → call LLM → save → consolidate. |
| `episodic.py` | The episodic memory vector store: `embed`, `add`, `retrieve` (top-k), `recent`, `all`, `count`, `sessions`. |
| `semantic.py` | Semantic memory: a flat JSON list of durable facts (`all`, `replace`). |
| `summarizer.py` | The summarizer agent: `consolidate(episodes, facts)` distills + reconciles the fact set. |
| `procedural.py` | Procedural memory: loads `skill.md` files, embeds their triggers, `select(message)` matches a skill or none. |
| `server.py` | FastAPI plumbing: cloud chat + local embed clients + stores; endpoints `/chat`, `/history?session=`, `/sessions`, `/facts`, `/consolidate`. |
| `static/index.html` | Chat UI + chat-list sidebar + facts panel + the live pipeline diagram. |
| `memory/procedural_memory/` | The skill files (source): `prompt_enhancer`, `idea_rater`, `idea_enhancer`. |
| `test_agent.py`, `test_semantic.py`, `test_summarizer.py` | Tests (no network, no Chroma). |
| `docs/` | The step diagrams, scraped Ollama API docs, and the memory improvement backlog. |

## Notes

- Memory lives in `memory/chroma/` (git-ignored). Delete that folder to start with
  a blank memory.
- Avoid `uvicorn --reload`: its child processes can be orphaned on interrupt and
  then hold port 8000 / lock the Chroma files. Use `--port 8000` without `--reload`.
