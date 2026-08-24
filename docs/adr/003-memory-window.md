# ADR-003: Sliding-window memory and horizontal truncation

**Date:** 2026-08-23  
**Status:** Accepted

## Context

Long TDD traces overflow small context windows. Huge `read_file` / pytest
blobs overflow even faster.

## Decision

- Truncate any observation over 3,000 characters (head + tail).
- When `messages` exceeds `max_memory_items` (default 8), keep the original
  user prompt, a purge note, and the last four items.

## Consequences

The loop can run longer on sub-2B models. The agent may forget failed
approaches from early in the trace and repeat them.
