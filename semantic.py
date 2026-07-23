"""semantic.py - the semantic memory store (step-2.png).

Semantic memory = durable facts about the user ("drives a blue Tesla",
"prefers concise answers") and their profile. Unlike episodic memory, this set
is SMALL and always relevant, so we do NOT use a vector store or top-k search:
we keep a plain list of fact strings in one JSON file and inject ALL of them
into context every turn.

The summarizer agent (summarizer.py) is what writes here: after N chats it reads
the episodes, distills them into facts, resolves contradictions, and REPLACES
the whole list. This file just loads and saves that list.
"""

import json
from pathlib import Path

# Where the durable facts persist on disk.
DEFAULT_FACTS_PATH = "memory/facts.json"


class SemanticStore:
    """A flat, on-disk list of durable facts about the user.

    No embeddings and no search - the fact set is small enough to load whole
    and inject in full. Persisted as JSON so it survives a restart.
    """

    def __init__(self, path: str = DEFAULT_FACTS_PATH):
        self.path = Path(path)

    def all(self) -> list[str]:
        """Return the current durable facts (empty list if none saved yet)."""
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def replace(self, facts: list[str]) -> None:
        """Overwrite the whole fact set - this is how consolidation reconciles."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(facts, indent=2), encoding="utf-8")
