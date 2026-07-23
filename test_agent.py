"""Tests for the agent (the harness).

These run WITHOUT the network and WITHOUT Chroma: we pass the agent fakes
(instead of the cloud chat model, the vector store, the fact store, and the
summarizer). That isolates the agent's logic - the pipeline steps, the hybrid
context (facts + retrieved + recent), de-duplication, saving each turn with its
chat, and the periodic consolidation.

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
    saves so we can assert the turn was persisted with its session. `count`
    drives the periodic-consolidation check; `all` feeds the summarizer.
    """

    def __init__(self, to_retrieve=None, recent=None, count=1, all_=None):
        self.to_retrieve = to_retrieve or []
        self._recent = recent or []
        self._count = count
        self._all = all_ or []
        self.added = []

    def retrieve(self, query, k):
        return self.to_retrieve

    def recent(self, session_id, n):
        return self._recent

    def add(self, user, assistant, session_id):
        self.added.append({"user": user, "assistant": assistant, "session_id": session_id})

    def count(self):
        return self._count

    def all(self, session_id=None):
        return self._all


class FakeSemantic:
    """Stand-in for the facts store: returns preset facts, records replacements."""

    def __init__(self, facts=None):
        self._facts = facts or []
        self.replaced = None

    def all(self):
        return self._facts

    def replace(self, facts):
        self.replaced = facts


class FakeSummarizer:
    """Stand-in for the summarizer: returns fixed facts, records its inputs."""

    def __init__(self, facts=None):
        self._facts = facts if facts is not None else ["a distilled fact"]
        self.called_with = None

    def consolidate(self, episodes, current_facts):
        self.called_with = (episodes, current_facts)
        return self._facts


class FakeProcedural:
    """Stand-in for the skill store: returns a preset selection, records the query."""

    def __init__(self, matched=False, name=None, body=None, distance=1.5):
        self._result = {"matched": matched, "name": name, "distance": distance, "body": body}
        self.selected = None

    def select(self, message):
        self.selected = message
        return self._result


def make_agent(client=None, store=None, semantic=None, summarizer=None, procedural=None):
    """Build a ChatAgent with fakes, defaulting the ones a test doesn't care about."""
    return ChatAgent(
        client=client or FakeClient(),
        store=store or FakeStore(),
        semantic=semantic or FakeSemantic(),
        summarizer=summarizer or FakeSummarizer(),
        procedural=procedural or FakeProcedural(),
    )


def contents(messages):
    """Just the user-message contents, for easy assertions."""
    return [m["content"] for m in messages if m["role"] == "user"]


def systems(messages):
    """Just the system-message contents."""
    return [m["content"] for m in messages if m["role"] == "system"]


def test_build_context_order_system_facts_retrieved_recent_then_user():
    """Context = system, facts, then retrieved, then recent, then the new message."""
    a = make_agent()
    retrieved = [{"user": "old memory", "assistant": "ok"}]
    recent = [{"user": "recent turn", "assistant": "sure"}]
    context = a.build_context("new question", ["drives a blue Tesla"], None, retrieved, recent)

    assert context[0]["role"] == "system"
    assert context[1]["role"] == "system"
    assert "drives a blue Tesla" in context[1]["content"]
    assert contents(context) == ["old memory", "recent turn", "new question"]


def test_no_facts_means_no_second_system_block():
    """With no durable facts and no skill, only the fixed system prompt is present."""
    a = make_agent()
    context = a.build_context("hi", [], None, [], [])
    assert len(systems(context)) == 1


def test_matched_skill_is_injected_as_system_block():
    """A matched skill body is injected as its own system block; none means none."""
    a = make_agent()
    with_skill = a.build_context("x", [], "PROCEDURE: do the thing", [], [])
    assert any("PROCEDURE: do the thing" in s for s in systems(with_skill))

    without = a.build_context("x", [], None, [], [])
    assert not any("PROCEDURE" in s for s in systems(without))


def test_run_yields_stages_in_diagram_order():
    """The pipeline events follow the step-2 order (semantic after retrieve)."""
    a = make_agent()
    stages = [e["name"] for e in a.run("hello", "s1") if e["type"] == "stage"]
    assert stages == ["user_prompt", "retrieve", "semantic", "procedural", "context", "llm", "reply", "episodic"]


def test_facts_reach_the_model_as_a_system_block():
    """Durable facts are injected into context every turn (always present)."""
    client = FakeClient()
    a = make_agent(client=client, semantic=FakeSemantic(["drives a blue Tesla"]))
    list(a.run("what do i drive?", "s1"))

    assert any("drives a blue Tesla" in s for s in systems(client.received_messages))


def test_matched_skill_reaches_the_model():
    """When a skill matches, its procedure is sent to the model as a system block."""
    client = FakeClient()
    procedural = FakeProcedural(matched=True, name="idea_rater", body="Score the idea 1-10")
    a = make_agent(client=client, procedural=procedural)
    list(a.run("rate my idea", "s1"))

    assert procedural.selected == "rate my idea"
    assert any("Score the idea 1-10" in s for s in systems(client.received_messages))


def test_retrieved_and_recent_reach_the_model():
    """Both retrieved memories and recent turns must appear in the LLM messages."""
    client = FakeClient()
    store = FakeStore(
        to_retrieve=[{"id": "a", "user": "I like teal", "assistant": "ok"}],
        recent=[{"id": "b", "user": "hello again", "assistant": "hi"}],
    )
    a = make_agent(client=client, store=store)
    list(a.run("what do i like?", "s1"))

    sent = contents(client.received_messages)
    assert "I like teal" in sent
    assert "hello again" in sent


def test_retrieved_duplicate_of_recent_is_dropped():
    """An episode in both retrieve and recent (same id) is not sent twice."""
    client = FakeClient()
    same = {"id": "x", "user": "my name is Sam", "assistant": "noted"}
    store = FakeStore(to_retrieve=[same], recent=[same])
    a = make_agent(client=client, store=store)
    list(a.run("hi", "s1"))

    assert contents(client.received_messages).count("my name is Sam") == 1


def test_turn_is_saved_with_its_session():
    """After a turn, the exchange is saved tagged with the chat's session_id."""
    store = FakeStore()
    a = make_agent(store=store)
    list(a.run("hello", "chat-42"))

    assert store.added == [{"user": "hello", "assistant": "Hi there", "session_id": "chat-42"}]


def test_error_is_reported_and_nothing_saved():
    """If the LLM call fails, we get an error event and save nothing."""
    store = FakeStore()
    a = make_agent(client=BrokenClient(), store=store)
    events = list(a.run("hello", "s1"))

    assert events[-1] == {"type": "error", "message": "boom"}
    assert store.added == []


def test_consolidates_every_n_exchanges():
    """When the episode count hits a multiple of N, the summarizer runs."""
    store = FakeStore(count=agent_module.CONSOLIDATE_EVERY, all_=[{"user": "u", "assistant": "a"}])
    semantic = FakeSemantic(["old fact"])
    summarizer = FakeSummarizer(["reconciled fact"])
    a = make_agent(store=store, semantic=semantic, summarizer=summarizer)

    stages = [e["name"] for e in a.run("hello", "s1") if e["type"] == "stage"]
    assert "consolidate" in stages
    assert summarizer.called_with == ([{"user": "u", "assistant": "a"}], ["old fact"])
    assert semantic.replaced == ["reconciled fact"]


def test_does_not_consolidate_off_the_interval():
    """When the count is not a multiple of N, the summarizer does not run."""
    store = FakeStore(count=agent_module.CONSOLIDATE_EVERY - 1)
    summarizer = FakeSummarizer()
    a = make_agent(store=store, summarizer=summarizer)

    stages = [e["name"] for e in a.run("hello", "s1") if e["type"] == "stage"]
    assert "consolidate" not in stages
    assert summarizer.called_with is None
