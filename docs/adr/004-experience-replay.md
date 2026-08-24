# ADR-004: Trajectory abstraction (experience replay)

**Date:** 2026-08-23  
**Status:** Partially implemented

## Context

Successful traces vanished when the process exited. No measurable growth.

## Decision

On success, a reflection pass synthesizes a heuristic into `knowledge.json`.
Future calls inject those rules into the system prompt.

## Consequences

The runtime can "remember" environment gotchas without fine-tuning. The prompt
grows; retrieval will be required eventually. This is still not RSI.
