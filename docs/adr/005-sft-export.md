# ADR-005: Trajectory serialization for SFT

**Date:** 2026-08-23  
**Status:** Proposed pipeline (export exists, training does not)

## Context

Prompt injection of heuristics does not change the base model. JSON schema
errors repeat forever.

## Decision

- Export verified rollouts as JSONL (`dataset.jsonl` / `data/train.jsonl`).
- Train LoRA offline (e.g. Apple MLX), fuse, load in Ollama.

## Consequences

A path to weight-level improvement exists. This repository does not run
training for you. Expect downtime while swapping checkpoints.
