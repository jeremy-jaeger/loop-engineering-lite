# ADR-001: Self-correction loop for tool enforcement

**Date:** 2026-08-23  
**Status:** Accepted

## Context

With local Qwen-class models the agent often *described* a tool use, set
`status: complete`, and returned `None`. The loop exited without doing the task.

## Decision

Enforce tools in the prompt **and** in the engine:

- System prompt forbids narrating actions without a `tool_call`.
- If `complete` arrives without a passing verification command, inject an
  error and retry (ADR-006). Empty `final_answer` after a verified run is
  filled in by the harness.

## Consequences

Lazy completions are much rarer. Stuck models burn iterations until
`max_iterations`.
