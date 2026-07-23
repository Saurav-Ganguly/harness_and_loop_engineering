"""server.py - the web plumbing.

This file connects the browser to the agent. It knows nothing about how the
agent thinks - it only:

    1. serves the web page (static/index.html)
    2. receives a chat message from the browser
    3. runs agent.run() and forwards each event to the browser as it happens,
       using Server-Sent Events (SSE) - a simple one-way "server keeps sending"
       stream that JavaScript can read live.

Run it with:  uv run uvicorn server:app --reload
"""

import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from ollama import Client

from agent import ChatAgent
from episodic import EpisodicStore
from procedural import ProceduralStore
from semantic import SemanticStore
from summarizer import Summarizer

# Load variables from the .env file into the environment.
# We never read .env directly - we just ask for the value by name.
load_dotenv()

# The CHAT model runs on the cloud (ollama.com), using your API key from
# .env as: ollama_key=your_key
API_KEY = os.environ["ollama_key"]
chat_client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {API_KEY}"},
)

# The EMBEDDING model runs LOCALLY (Ollama cloud has no embedding model), so
# this client talks to the local daemon at http://localhost:11434 - no key.
embed_client = Client()

# Episodic memory: a vector store the agent reads from and writes to.
store = EpisodicStore(embed_client=embed_client)

# Semantic memory: a flat file of durable facts, always injected into context.
semantic = SemanticStore()

# Procedural memory: skill.md files matched to a message by embedding similarity.
# Embeds each skill's description once (via the local embed client), then the
# matched skill's procedure is injected into context.
procedural = ProceduralStore(embed_client=embed_client)

# The summarizer distills episodes into reconciled facts. It runs on the CLOUD
# (gemma4) - the local model was too slow. Cloud ignores structured outputs, so
# the summarizer parses one-fact-per-line text instead.
summarizer = Summarizer(client=chat_client)

# One agent for this running server. Its memory now lives on disk in the stores.
# It auto-consolidates via the summarizer every N turns; "Consolidate" runs it now.
agent = ChatAgent(
    client=chat_client, store=store, semantic=semantic, summarizer=summarizer, procedural=procedural
)

app = FastAPI()


@app.get("/")
def index():
    """Serve the single-page UI."""
    return FileResponse("static/index.html")


@app.get("/history")
def history(session: str | None = None):
    """Return one chat's episodes as a flat list of chat bubbles.

    Pass ?session=<id> to get just that chat (what the visible thread shows).
    Each stored episode holds a user+assistant pair; we flatten it into
    {role, content} bubbles so the browser can rebuild the chat on load.
    """
    bubbles = []
    for episode in store.all(session):
        bubbles.append({"role": "user", "content": episode["user"]})
        bubbles.append({"role": "assistant", "content": episode["assistant"]})
    return bubbles


@app.get("/sessions")
def sessions():
    """List all chats (id, title, start time, count) so the UI can show them."""
    return store.sessions()


@app.get("/facts")
def facts():
    """Return the current durable facts (semantic memory) for the UI panel."""
    return semantic.all()


@app.post("/consolidate")
def consolidate():
    """Run the summarizer now: distill all episodes into reconciled facts.

    Reads every episode plus the current facts, replaces the fact set with the
    summarizer's reconciled output, and returns it. This is the manual button;
    the agent also does this automatically every N turns.
    """
    episodes = store.all()
    new_facts = summarizer.consolidate(episodes, semantic.all())
    semantic.replace(new_facts)
    return new_facts


def to_sse(events) -> str:
    """Turn each agent event dict into SSE wire format: `data: <json>\\n\\n`."""
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


@app.post("/chat")
async def chat(request: Request):
    """Receive a message (with its chat's session_id) and stream pipeline events."""
    body = await request.json()
    user_message = body["message"]
    session_id = body["session_id"]
    return StreamingResponse(
        to_sse(agent.run(user_message, session_id)),
        media_type="text/event-stream",
    )
