"""agent.py - the "harness" (the box in step-2.png).

This file is the actual agent. It knows nothing about the web. Its job:

    your new message
        -> RETRIEVE the most relevant past episodes from memory, across all
           chats (RAG), PLUS the recent turns of the current chat
        -> assemble system prompt + retrieved + recent + your message ("context")
        -> send to the LLM
        -> stream back the reply
        -> SAVE this new exchange into episodic memory, tagged with this chat

As it does each step, it "yields" a small event (a plain dict) so the web
server can light up the matching box in the diagram.

Context is a HYBRID: retrieved memories (relevant, from any chat) give long-term
recall, while the recent-turns window (this chat, verbatim) keeps the current
conversation coherent. We never send the whole history - only these two pieces.
"""

import time

# The system prompt: the agent's fixed instructions, sent on every turn.
SYSTEM_PROMPT = "You are a helpful, concise assistant."

# The cloud chat model, from https://ollama.com/library/deepseek-v4-flash
MODEL = "deepseek-v4-flash"

# How many relevant past episodes to pull into context each turn (the "k" in top-k).
RETRIEVE_K = 3

# How many recent exchanges of the CURRENT chat to always include (for continuity).
RECENT_EXCHANGES = 3

# How many exchanges before the summarizer auto-consolidates episodes into facts.
CONSOLIDATE_EVERY = 5

# A small pause per step so you can watch the boxes light up in the browser.
STAGE_DWELL_SECONDS = 0.3


class ChatAgent:
    """Runs one turn at a time, using a vector store for memory.

    Pass a `client` (the cloud ollama Client for chat) and a `store` (an
    EpisodicStore for memory). Both are injected, so tests can pass fakes and
    run without the network.
    """

    def __init__(self, client, store, semantic, summarizer, procedural):
        self.client = client
        self.store = store
        self.semantic = semantic
        self.summarizer = summarizer
        self.procedural = procedural

    def build_context(
        self,
        user_message: str,
        facts: list[str],
        skill_body: str | None,
        retrieved: list[dict],
        recent: list[dict],
    ) -> list[dict]:
        """Assemble the messages we send to the model.

        = system prompt, then durable facts (semantic memory) as a SEPARATE
        system block, then the matched skill (procedural memory) as its own
        system block, then retrieved memories (relevant, from any chat), then
        the recent turns of the current chat, then the new message. The episode
        blocks are replayed as real user/assistant turns, oldest first.
        """
        context = [{"role": "system", "content": SYSTEM_PROMPT}]
        if facts:
            context.append({
                "role": "system",
                "content": "What you know about the user:\n" + "\n".join(f"- {f}" for f in facts),
            })
        if skill_body:
            context.append({
                "role": "system",
                "content": "Follow this procedure for the user's request:\n\n" + skill_body,
            })
        for episode in retrieved + recent:
            context.append({"role": "user", "content": episode["user"]})
            context.append({"role": "assistant", "content": episode["assistant"]})
        context.append({"role": "user", "content": user_message})
        return context

    def run(self, user_message: str, session_id: str):
        """Run one chat turn, yielding events that mirror the step-2 diagram.

        Box names: user_prompt, retrieve, context, llm, reply, episodic.
        """
        # Step 1: we received the user's prompt.
        yield {"type": "stage", "name": "user_prompt"}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 2: retrieve relevant memories (any chat) + this chat's recent turns.
        retrieved = self.store.retrieve(user_message, k=RETRIEVE_K)
        recent = self.store.recent(session_id, RECENT_EXCHANGES)
        # Drop any retrieved episode that is already in the recent window (no dupes).
        recent_ids = {episode["id"] for episode in recent}
        retrieved = [episode for episode in retrieved if episode["id"] not in recent_ids]
        yield {"type": "stage", "name": "retrieve"}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 3: load durable facts from semantic memory (always in context).
        facts = self.semantic.all()
        yield {"type": "stage", "name": "semantic"}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 4: pick a procedural skill for this message (or none if nothing fits).
        # We report the nearest candidate + distance either way so the UI can show
        # both a match and a near-miss.
        skill = self.procedural.select(user_message)
        yield {"type": "stage", "name": "procedural", "matched": skill["matched"],
               "skill": skill["name"], "distance": skill["distance"]}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 5: assemble system prompt + facts + skill + retrieved + recent + new message.
        context = self.build_context(user_message, facts, skill["body"], retrieved, recent)
        yield {"type": "stage", "name": "context"}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 4: call the LLM and stream the reply back piece by piece.
        yield {"type": "stage", "name": "llm"}
        reply_parts: list[str] = []
        try:
            for chunk in self.client.chat(model=MODEL, messages=context, stream=True):
                piece = chunk["message"]["content"]
                reply_parts.append(piece)
                yield {"type": "token", "text": piece}
        except Exception as error:
            # Any failure (bad key, model down, no network) surfaces here.
            yield {"type": "error", "message": str(error)}
            return

        # Step 5: the reply is complete.
        full_reply = "".join(reply_parts)
        yield {"type": "stage", "name": "reply"}
        time.sleep(STAGE_DWELL_SECONDS)

        # Step 6: save this exchange into episodic memory (embed + store),
        # tagged with this chat, so future turns (in any chat) can retrieve it.
        self.store.add(user_message, full_reply, session_id)
        yield {"type": "stage", "name": "episodic"}

        # Step 7: every N exchanges, the summarizer consolidates all episodes
        # into reconciled durable facts and replaces the semantic store.
        if self.store.count() % CONSOLIDATE_EVERY == 0:
            new_facts = self.summarizer.consolidate(self.store.all(), self.semantic.all())
            self.semantic.replace(new_facts)
            yield {"type": "stage", "name": "consolidate"}

        yield {"type": "done"}
