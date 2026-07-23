# Memory system - improvement backlog

Deferred improvements to the Step 2 memory system, captured 2026-07-23.
Ordered by priority. The current design works; these make it scale and stay honest.

## 1. Incremental (watermarked) consolidation - the real fix

**Problem.** Consolidation re-reads *every* episode and *fully rewrites* the whole
fact set each time ([agent.py](../agent.py) `summarizer.consolidate(self.store.all(), ...)`).
Two issues, present even at ~30 episodes:

- **O(entire history) per run.** Every 5 turns the whole transcript goes back into
  the summarizer - mostly re-summarizing already-summarized turns. Huge prompts at scale.
- **Full-rewrite is lossy and non-deterministic.** Each run rewrites all facts from
  scratch: the model can silently drop or reword a good fact, with no way to know why
  a fact disappeared. For a memory system, losing provenance is the scariest property.

**Fix.** Keep a **watermark** (cursor to the last-consolidated episode). Feed only the
episodes *since* the watermark, and treat the existing fact set as the accumulator to
merge into. Fixes both problems at once. This is the single upgrade that best teaches
how real memory consolidation works.

## 2. Honest consolidation trigger

`self.store.count() % 5 == 0` triggers on **total** episode count across all chats,
and re-consolidates all history every 5 total turns. Replace with a simple
"turns since last consolidation" counter (pairs with the watermark in #1). Low priority.

## 3. Relevance threshold on retrieval

top-k always returns k=3, even when nothing is actually relevant - cosine hands back
the 3 "least bad" and they get injected as if authoritative. Add a distance/similarity
threshold so irrelevant episodes are dropped. Defer.

## 4. Cap / prune growing facts

Every fact is injected into every prompt forever. Fine at ~10 facts, context bloat at
~200. Later: cap the fact count, or add relevance retrieval / hierarchical facts. Defer.

## 5. Local-Ollama hard dependency

The whole system stalls if local Ollama (embeddings) is down - the "hi got stuck" bug.
Accepted tradeoff for now (Ollama cloud has no embedding model). Revisit if it bites.
