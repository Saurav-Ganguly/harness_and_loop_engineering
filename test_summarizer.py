"""test_summarizer.py - tests for the summarizer agent.

No network: we pass a FakeClient that returns a fixed reply, so we test the
prompt assembly and the line parsing, not the model.
"""

from summarizer import Summarizer, parse_facts


class FakeClient:
    """Stand-in for the cloud chat client: returns a fixed non-streamed reply."""

    def __init__(self, content):
        self.content = content
        self.received = None

    def chat(self, model, messages, stream):
        self.received = messages
        return {"message": {"content": self.content}}


def test_parse_facts_strips_bullets_and_blanks():
    text = "- drives a blue Tesla\n\n* prefers concise answers\n"
    assert parse_facts(text) == ["drives a blue Tesla", "prefers concise answers"]


def test_consolidate_returns_parsed_facts():
    client = FakeClient("name is Saurav\ndrives a blue Tesla")
    facts = Summarizer(client=client).consolidate(
        episodes=[{"user": "I drive a blue Tesla", "assistant": "nice"}],
        current_facts=["drives a red Tesla"],
    )
    assert facts == ["name is Saurav", "drives a blue Tesla"]


def test_consolidate_sends_current_facts_and_episodes_to_model():
    """The prompt must contain both the known facts and the new conversation."""
    client = FakeClient("x")
    Summarizer(client=client).consolidate(
        episodes=[{"user": "I drive a blue Tesla", "assistant": "nice"}],
        current_facts=["drives a red Tesla"],
    )
    sent = client.received[-1]["content"]
    assert "drives a red Tesla" in sent  # current facts reach the model
    assert "blue Tesla" in sent          # the new episode reaches the model
