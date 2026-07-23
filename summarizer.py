"""summarizer.py - the summarizer agent (step-2.png).

A cheaper CLOUD model (gemma4) that DISTILLS episodes into durable facts and
RECONCILES them against the facts we already have. It reads every past exchange
plus the current fact list, then returns the full, updated fact set - so a
contradiction (a red Tesla, then a blue one) collapses into a single current
fact instead of two coexisting ones.

The result REPLACES the semantic store (semantic.py). Ollama Cloud ignores the
structured-output `format` param (verified - it returns plain text anyway), so
we ask for one fact per line and parse the lines - simple and robust.
"""

# The cheaper cloud model that does the distilling (swappable in one line).
SUMMARIZER_MODEL = "gemma4:cloud"

SUMMARIZER_SYSTEM = (
    "You maintain a user's long-term memory. You are given the facts known so "
    "far and a transcript of recent conversations. Return the COMPLETE, updated "
    "list of durable facts about the user.\n"
    "Rules:\n"
    "- Keep only lasting facts: identity, preferences, belongings, goals. Drop "
    "small talk and one-off questions.\n"
    "- When a new statement contradicts an old fact, keep only the NEW one.\n"
    "- Merge duplicates. Keep each fact short.\n"
    "- Output ONE fact per line. No numbering, no bullets, no extra text."
)


def parse_facts(text: str) -> list[str]:
    """One fact per line: strip any stray bullet, drop blank lines."""
    facts = []
    for line in text.splitlines():
        line = line.strip()
        for bullet in ("- ", "* ", "• "):
            if line.startswith(bullet):
                line = line[len(bullet):].strip()
        if line:
            facts.append(line)
    return facts


class Summarizer:
    """Distills episodes into reconciled durable facts using a cheap LLM.

    Pass a `client` (the cloud ollama Client). It is injected so tests can pass
    a fake and run without the network.
    """

    def __init__(self, client, model: str = SUMMARIZER_MODEL):
        self.client = client
        self.model = model

    def consolidate(self, episodes: list[dict], current_facts: list[str]) -> list[str]:
        """Return the updated fact set from all episodes + the current facts."""
        transcript = "\n".join(
            f"User: {e['user']}\nAssistant: {e['assistant']}" for e in episodes
        )
        known = "\n".join(current_facts) if current_facts else "(none yet)"
        prompt = f"Facts known so far:\n{known}\n\nRecent conversations:\n{transcript}"
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SUMMARIZER_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return parse_facts(response["message"]["content"])
