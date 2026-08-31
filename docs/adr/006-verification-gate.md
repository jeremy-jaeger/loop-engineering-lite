# ADR-006: Gate reality and learning on binary verification

**Date:** 2026-08-24  
**Status:** Accepted / implemented

## Context

`complete` used to commit and export when the model said so, including via
`len(messages) > 3`. That poisons `knowledge.json` and any SFT set.

## Decision

- `commit_to_reality` only if the last command is a passing pytest/unittest.
- Export `{messages, reward, task, verified_command}` with `reward ∈ {0.0, 1.0}`.
- Empty `final_answer` is filled in only after `[SIMULATION VERIFIED SUCCESS]`.
- Commit only agent-touched paths.
- Failed runs go to `data/rejected.jsonl`.

## Consequences

Failed TDD no longer writes the host tree. Weight training can consume an honest
chosen/rejected pair. Many loops will `[ABORT]` until tests actually pass.
