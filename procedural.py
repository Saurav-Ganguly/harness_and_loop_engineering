"""procedural.py - the procedural memory store (step-2.png).

Procedural memory = HOW to do a task. Each skill is a folder under
`memory/procedural_memory/<skill>/skill.md`: a small file with a `name` and a
`description` (its trigger) in YAML frontmatter, then a body that spells out the
procedure to follow.

Selecting a skill is just retrieval again: we embed each skill's `description`
once, embed the incoming message, and take the nearest one - but ONLY if it is
close enough (a distance threshold). If nothing clears the bar, no skill fires.
This is the "match one skill, or match none" engine.

Bodies are read fresh from disk on startup (so editing a procedure needs no
re-embed); only the description embeddings live in Chroma, keyed by skill name,
and we add only names not already stored. The embedding model runs LOCALLY,
same as episodic memory.
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings

from episodic import DEFAULT_DB_PATH, EMBED_MODEL

# Where the skill folders live, and the Chroma collection for their embeddings.
DEFAULT_SKILLS_DIR = "memory/procedural_memory"
COLLECTION = "procedural"

# Max distance for a match. Chroma's default is squared-L2; with embeddinggemma's
# normalized vectors that is 2 - 2*cos, so 0 = identical, 2 = unrelated. Anything
# farther than this is treated as "no skill applies." Calibrated empirically: real
# triggers measured 0.86-1.08, near-miss/noise 1.24+, so 1.15 sits in the gap.
MATCH_MAX_DISTANCE = 1.15


def parse_skill(text: str) -> tuple[str, str, str]:
    """Split a skill.md into (name, description, body).

    Frontmatter is the block between the first two `---` fences; the body is
    everything after it. Simple line parsing - no YAML dependency needed.
    """
    parts = text.split("---")
    frontmatter = parts[1] if len(parts) > 2 else ""
    body = "---".join(parts[2:]).strip() if len(parts) > 2 else text.strip()
    name = description = ""
    for line in frontmatter.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            name = line[len("name:"):].strip()
        elif line.startswith("description:"):
            description = line[len("description:"):].strip()
    return name, description, body


class ProceduralStore:
    """Skills (how-to procedures) matched to a message by embedding similarity.

    Pass an `embed_client` (a local ollama Client). Skill bodies are loaded from
    disk; description embeddings are cached in Chroma so we embed each skill once.
    """

    def __init__(
        self,
        embed_client,
        skills_dir: str = DEFAULT_SKILLS_DIR,
        db_path: str = DEFAULT_DB_PATH,
        model: str = EMBED_MODEL,
        threshold: float = MATCH_MAX_DISTANCE,
    ):
        self.embed_client = embed_client
        self.model = model
        self.threshold = threshold
        client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        self.collection = client.get_or_create_collection(name=COLLECTION)
        self.skills = self._load_skills(skills_dir)
        self._sync_embeddings()

    def embed(self, text: str) -> list[float]:
        """Turn text into a vector using the local Ollama embedding model."""
        return self.embed_client.embed(model=self.model, input=text)["embeddings"][0]

    def _load_skills(self, skills_dir: str) -> dict[str, dict]:
        """Read every <skill>/skill.md from disk into {name: {description, body}}."""
        skills: dict[str, dict] = {}
        for skill_md in sorted(Path(skills_dir).glob("*/skill.md")):
            name, description, body = parse_skill(skill_md.read_text(encoding="utf-8"))
            if name:
                skills[name] = {"description": description, "body": body}
        return skills

    def _sync_embeddings(self) -> None:
        """Embed and store any skill whose name is not already in the collection."""
        existing = set(self.collection.get()["ids"])
        for name, skill in self.skills.items():
            if name not in existing:
                self.collection.add(
                    ids=[name],
                    embeddings=[self.embed(skill["description"])],
                    documents=[skill["description"]],
                )

    def select(self, message: str) -> dict:
        """Pick the best skill for a message, or none if nothing clears the bar.

        Returns {"matched", "name", "distance", "body"}. On a match, `body` is the
        skill's procedure to inject; otherwise `body` is None but `name`/`distance`
        still report the nearest candidate (handy for the UI and tuning).
        """
        if self.collection.count() == 0:
            return {"matched": False, "name": None, "distance": None, "body": None}
        result = self.collection.query(query_embeddings=[self.embed(message)], n_results=1)
        name = result["ids"][0][0]
        distance = result["distances"][0][0]
        matched = distance <= self.threshold and name in self.skills
        body = self.skills[name]["body"] if matched else None
        return {"matched": matched, "name": name, "distance": distance, "body": body}
