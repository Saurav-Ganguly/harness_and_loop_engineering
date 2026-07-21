"""Tests for the agent (the harness).

These run WITHOUT the network and WITHOUT Chroma: we pass the agent a FakeClient
(instead of the cloud chat model) and a FakeStore (instead of the vector store).
That isolates the agent's logic - the pipeline steps, the hybrid context
(retrieved + recent), de-duplication, and that each turn is saved with its chat.

Run with:  uv run pytest
"""

import agent as agent_module
from agent import ChatAgent

# The dwell is just a visual delay for the browser; skip it so tests are fast.
agent_module.STAGE_DWELL_SECONDS = 0.0


class FakeClient:
    """Stand-in for the cloud chat client: streams a fixed two-piece reply."""

    def __init__(self):
        self.received_messages = None

    def chat(self, model, messages, stream):
        self.received_messages = messages
        yield {"message": {"content": "Hi"}}
        yield {"message": {"content": " there"}}


class BrokenClient:
    """A chat client that fails, to test error handling."""

    def chat(self, model, messages, stream):
        raise RuntimeError("boom")


class FakeStore:
    """Stand-in for the vector store.

    `retrieve` / `recent` return whatever episodes we preload; `add` records
    saves so we can assert the turn was persisted with its session.
    """

    def __init__(self, to_retrieve=None, recent=None):
        self.to_retrieve = to_retrieve or []
        self._recent = recent or []
        self.added = []

    def retrieve(self, query, k):
        return self.to_retrieve

    def recent(self, session_id, n):
        return self._recent

    def add(self, user, assistant, session_id):
        self.added.append({"user": user, "assistant": assistant, "session_id": session_id})


def contents(messages):
    """Just the user-message contents, for easy assertions."""
    return [m["content"] for m in messages if m["role"] == "user"]


def test_build_context_order_system_retrieved_recent_then_user():
    """Context = system, then retrieved, then recent, then the new message."""
    a = ChatAgent(client=FakeClient(), store=FakeStore())
    retrieved = [{"user": "old memory", "assistant": "ok"}]
    recent = [{"user": "recent turn", "assistant": "sure"}]
    context = a.build_context("new question", retrieved, recent)

    assert context[0]["role"] == "system"
    assert contents(context) == ["old memory", "recent turn", "new question"]


def test_run_yields_stages_in_diagram_order():
    """The pipeline events follow the step-2 order (retrieve before context)."""
    a = ChatAgent(client=FakeClient(), store=FakeStore())
    stages = [e["name"] for e in a.run("hello", "s1") if e["type"] == "stage"]
    assert stages == ["user_prompt", "retrieve", "context", "llm", "reply", "episodic"]


def test_retrieved_and_recent_reach_the_model():
    """Both retrieved memories and recent turns must appear in the LLM messages."""
    client = FakeClient()
    store = FakeStore(
        to_retrieve=[{"id": "a", "user": "I like teal", "assistant": "ok"}],
        recent=[{"id": "b", "user": "hello again", "assistant": "hi"}],
    )
    a = ChatAgent(client=client, store=store)
    list(a.run("what do i like?", "s1"))

    sent = contents(client.received_messages)
    assert "I like teal" in sent
    assert "hello again" in sent


def test_retrieved_duplicate_of_recent_is_dropped():
    """An episode in both retrieve and recent (same id) is not sent twice."""
    client = FakeClient()
    same = {"id": "x", "user": "my name is Sam", "assistant": "noted"}
    store = FakeStore(to_retrieve=[same], recent=[same])
    a = ChatAgent(client=client, store=store)
    list(a.run("hi", "s1"))

    assert contents(client.received_messages).count("my name is Sam") == 1


def test_turn_is_saved_with_its_session():
    """After a turn, the exchange is saved tagged with the chat's session_id."""
    store = FakeStore()
    a = ChatAgent(client=FakeClient(), store=store)
    list(a.run("hello", "chat-42"))

    assert store.added == [{"user": "hello", "assistant": "Hi there", "session_id": "chat-42"}]


def test_error_is_reported_and_nothing_saved():
    """If the LLM call fails, we get an error event and save nothing."""
    store = FakeStore()
    a = ChatAgent(client=BrokenClient(), store=store)
    events = list(a.run("hello", "s1"))

    assert events[-1] == {"type": "error", "message": "boom"}
    assert store.added == []
