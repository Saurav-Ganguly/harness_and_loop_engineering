"""episodic.py - the episodic memory store, a VECTOR store (step-2.png).

Episodic memory = everything that happened, as searchable "episodes." Each
episode is one user+assistant exchange, tagged with the chat (`session_id`) it
belongs to. We:

    1. turn the exchange text into a vector (an embedding) with a local Ollama
       embedding model,
    2. store that vector + the text + metadata (session_id, timestamp) in Chroma,
    3. later, retrieve the most relevant past episodes by embedding the new
       question and asking Chroma for the nearest vectors (top-k search).

Retrieval searches ACROSS all chats (memory is shared), but each chat can also
list just its own turns via `all(session_id)` / `recent(session_id, n)`.
The embedding model runs LOCALLY; the chat model runs on the cloud (server.py).
"""

from datetime import datetime, timezone
from uuid import uuid4

import chromadb
from chromadb.config import Settings

# Recommended local embedding model (https://docs.ollama.com/capabilities/embeddings).
# It returns L2-normalized vectors, so "closeness" behaves like cosine similarity.
EMBED_MODEL = "embeddinggemma"

# Where the vector DB persists on disk, and the collection (table) name inside it.
DEFAULT_DB_PATH = "memory/chroma"
COLLECTION = "episodes"


def now_timestamp() -> str:
    """The current time as an ISO 8601 UTC string."""
    return datetime.now(timezone.utc).isoformat()


class EpisodicStore:
    """A vector store of past exchanges, backed by Chroma.

    Pass an `embed_client` (a local ollama Client) so this class can turn text
    into vectors. Everything is stored on disk, so it survives a restart.
    """

    def __init__(self, embed_client, db_path: str = DEFAULT_DB_PATH, model: str = EMBED_MODEL):
        self.embed_client = embed_client
        self.model = model
        # Persistent = saved to disk. Telemetry off to keep our logs clean.
        client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        # We always supply our own embeddings, so Chroma never embeds for us.
        self.collection = client.get_or_create_collection(name=COLLECTION)

    def embed(self, text: str) -> list[float]:
        """Turn text into a vector using the local Ollama embedding model."""
        return self.embed_client.embed(model=self.model, input=text)["embeddings"][0]

    def add(self, user: str, assistant: str, session_id: str) -> None:
        """Store one user+assistant exchange as a single embedded episode."""
        text = f"User: {user}\nAssistant: {assistant}"
        metadata = {
            "user": user,
            "assistant": assistant,
            "session_id": session_id,
            "timestamp": now_timestamp(),
        }
        self.collection.add(
            ids=[uuid4().hex],
            embeddings=[self.embed(text)],
            documents=[text],
            metadatas=[metadata],
        )

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Return the k most relevant past episodes across ALL chats (top-k search).

        Each result is {..., "id", "distance"}; smaller distance = more similar.
        Returns [] when the store is empty.
        """
        count = self.collection.count()
        if count == 0:
            return []
        result = self.collection.query(query_embeddings=[self.embed(query)], n_results=min(k, count))
        episodes = []
        for id_, metadata, distance in zip(result["ids"][0], result["metadatas"][0], result["distances"][0]):
            episodes.append({**metadata, "id": id_, "distance": distance})
        # Present them oldest-first so the model reads them in the order they happened.
        return sorted(episodes, key=lambda e: e["timestamp"])

    def recent(self, session_id: str, n: int) -> list[dict]:
        """Return the last n episodes of one chat, oldest first (for continuity)."""
        stored = self.collection.get(where={"session_id": session_id})
        episodes = [{**meta, "id": id_} for id_, meta in zip(stored["ids"], stored["metadatas"])]
        episodes.sort(key=lambda e: e["timestamp"])
        return episodes[-n:]

    def all(self, session_id: str | None = None) -> list[dict]:
        """Return stored episodes (one chat if session_id given, else every chat)."""
        where = {"session_id": session_id} if session_id else None
        stored = self.collection.get(where=where)
        return sorted(stored["metadatas"], key=lambda e: e["timestamp"])

    def sessions(self) -> list[dict]:
        """List every chat: {session_id, title, started_at, count}, newest first.

        The title is the chat's first user message - used to label it in the UI.
        """
        groups: dict[str, dict] = {}
        for meta in self.collection.get()["metadatas"]:
            sid = meta.get("session_id", "legacy")
            group = groups.get(sid)
            if group is None:
                groups[sid] = {"session_id": sid, "title": meta["user"], "started_at": meta["timestamp"], "count": 1}
            else:
                group["count"] += 1
                if meta["timestamp"] < group["started_at"]:  # keep the earliest as the title
                    group["started_at"] = meta["timestamp"]
                    group["title"] = meta["user"]
        return sorted(groups.values(), key=lambda s: s["started_at"], reverse=True)
