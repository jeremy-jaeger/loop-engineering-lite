# ADR-004: Trajectory abstraction (experience replay)

**Date:** 2026-08-23  
**Status:** Accepted (heuristics only)

## Context

Successful traces vanished when the process exited. No measurable growth.

## Decision

On verified success, a reflection pass may synthesize a heuristic into
`knowledge.json`. Future calls inject those rules into the system prompt.
Failed runs do not reflect.

## Consequences

The runtime can remember environment gotchas without fine-tuning. The
prompt grows; retrieval will be required eventually. This is still not
recursive self-improvement of weights.
