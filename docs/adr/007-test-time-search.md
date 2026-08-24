# ADR-007: Verifier-guided test-time search

**Date:** 2026-08-24  
**Status:** Accepted / implemented

## Context

SFT on verified traces mostly teaches a 0.8B–2B model the JSON harness. It does
not search for solutions. Sub-2B policies need a cheap exact verifier over
counterfactual file states.

## Decision

- `VirtualFileSystem.fork()` / `adopt()` copy state without host writes.
- `SymbolicWorldModel.rollout` / `value` (value = last test score).
- Best-of-N: apply mutating tool calls on forks, score with pytest/unittest,
  adopt the winner.
- Winner/loser pairs go to `data/search_dpo.jsonl`.
- `run_agent_loop(..., search_width=K, verify_command=...)`. Default `K=1`.

## Consequences

Simulation-before-destruction is an API. Search multiplies `simulate_command`
cost. Swarm should reuse `fork()`, not replace search.
