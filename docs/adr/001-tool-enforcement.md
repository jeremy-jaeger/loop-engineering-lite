# ADR-001: Self-correction loop for tool enforcement

**Date:** 2026-08-23  
**Status:** Accepted

## Context

With local Qwen-class models the agent often *described* a tool use, set
`status: complete`, and returned `None`. The loop exited without doing the task.

## Decision

Enforce tools in the prompt **and** in the engine:

- System prompt forbids narrating actions without a `tool_call`.
- If `complete` arrives with an empty `final_answer`, inject an error and retry
  (unless a verified simulation already landed).

## Consequences

Lazy completions are much rarer. Stuck models burn iterations until
`max_iterations`.
