# ADR-005: Trajectory serialization for SFT

**Date:** 2026-08-23  
**Status:** Export implemented; training not vendored

## Context

Prompt injection of heuristics does not change the base model. JSON schema
errors repeat forever. Ungated export mixed failures into the SFT set.

## Decision

- Export verified rollouts as JSONL with `reward=1.0` (`dataset.jsonl`).
- Export aborts as `reward=0.0` (`data/rejected.jsonl`).
- Train LoRA offline (e.g. Apple MLX), fuse, load in Ollama via
  `OLLAMA_MODEL`.

## Consequences

A path to weight-level improvement exists. This repository does not run
training for you. Expect downtime while swapping checkpoints.
