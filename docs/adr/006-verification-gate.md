# ADR-006: Gate reality and learning on binary verification

**Date:** 2026-08-24  
**Status:** Accepted

## Context

`complete` used to commit and export when the model said so, including via
`len(messages) > 3` or an inference-error payload that faked `complete`.
That writes hallucinated files to disk and poisons `knowledge.json` /
`dataset.jsonl`.

## Decision

- `commit_to_reality` only if the last sandbox command is a passing
  pytest/unittest (or `python3 test_*.py`) run.
- Export `{messages, reward, task, verified_command}` with
  `reward ∈ {0.0, 1.0}`. Aborts go to `data/rejected.jsonl`.
- Empty `final_answer` is filled in only after a verified success.
- Commit only agent-touched paths. Substrate files the agent never wrote
  stay untouched.
- Writes are jailed to `base_dir`.
- Inference failures are retries, not completions.

## Consequences

Failed TDD no longer writes the host tree. A successful `python3 hello.py`
is not enough. Many loops will `[ABORT]` until tests actually pass. That
is the product.
