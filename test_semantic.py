"""test_semantic.py - tests for the semantic (durable facts) store.

No network and no Chroma - the store is just a JSON file, so we point it at a
temporary path.
"""

from semantic import SemanticStore


def test_empty_when_no_file(tmp_path):
    """A brand-new store (no file yet) has no facts."""
    store = SemanticStore(path=str(tmp_path / "facts.json"))
    assert store.all() == []


def test_replace_then_all_round_trips(tmp_path):
    """replace() saves the facts; all() reads them back."""
    store = SemanticStore(path=str(tmp_path / "facts.json"))
    store.replace(["drives a blue Tesla", "prefers concise answers"])
    assert store.all() == ["drives a blue Tesla", "prefers concise answers"]


def test_replace_overwrites_previous_facts(tmp_path):
    """Consolidation reconciles by replacing - the red Tesla becomes blue."""
    store = SemanticStore(path=str(tmp_path / "facts.json"))
    store.replace(["drives a red Tesla"])
    store.replace(["drives a blue Tesla"])
    assert store.all() == ["drives a blue Tesla"]


def test_persists_across_instances(tmp_path):
    """Facts survive a restart: a new store at the same path sees them."""
    path = str(tmp_path / "facts.json")
    SemanticStore(path=path).replace(["name is Saurav"])
    assert SemanticStore(path=path).all() == ["name is Saurav"]
