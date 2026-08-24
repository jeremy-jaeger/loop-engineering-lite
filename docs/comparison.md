# Comparison

This harness is a **small local loop** with one unusual constraint: file
writes reach the host only after a passing pytest or unittest run in a
tempdir copy of an in-memory VFS.

It is not a replacement for an IDE agent, a repo-wide SWE agent, or a
hosted coding assistant. Use the table to decide whether the constraint
is the thing you want.

| | Loop Engineering Lite | Aider | Mini-SWE-agent / SWE-agent | OpenHands | Continue / Cursor / Claude Code |
| --- | --- | --- | --- | --- | --- |
| Runs locally | Yes (Python + Ollama) | Yes | Mostly yes | Yes, heavier | Mixed; several are hosted |
| Runtime deps | Stdlib | Several | Several | Docker / runtime stack | Product-specific |
| Edits | In-memory VFS first | Live git tree | Live tools / sandbox | Sandbox / runtime | Live workspace |
| Commit / apply gate | Passing pytest/unittest | You / git | Task success heuristics | Runtime-dependent | You / the product |
| Model | Any Ollama chat model | Many providers | Many providers | Many providers | Product default |
| Typical job | Tiny TDD utilities, trace collection | Pair-program a real repo | GitHub issues, patches | Multi-tool agents | Daily IDE work |
| Surface area | `loop.py` is ~200 lines | Large | Large | Large | Closed or large |

## When to pick this

- You want **hallucinated code kept off disk** unless tests pass.
- You are collecting **reward-labeled traces** (`dataset.jsonl` vs
  `data/rejected.jsonl`) for later SFT / DPO.
- You are evaluating a **local** model on a binary verifier, not a chat
  vibe check.
- You want something you can read and fork in an afternoon.

## When to pick something else

- **Aider** — you already have a git repo and want a pair programmer that
  commits for real, with diffs you review.
- **SWE-agent / Mini-SWE-agent / OpenHands** — the unit of work is an
  issue, a PR, or a multi-file refactor, and you accept a larger stack.
- **Continue, Cursor, Claude Code, Codex** — you want inline IDE edits,
  repo Q&A, or a hosted agent with tools we do not implement (browser,
  GitHub, cloud sandboxes).
- **LangGraph / custom ReAct** — you need a framework, not a 200-line
  loop. You can still steal the VFS idea; that is the point of keeping
  the file small.

## What “lite” means here

The GitHub repo is named `loop-engineering-lite` because the **shipped
loop is small**, not because this is a teaser for a private product.
The [north star](NORTH_STAR.md) is written down so we do not pretend
the VFS is Dreamer.

## Honest gaps vs the rest of the field

- No container. `shell=True` in a tempdir. Read [SECURITY.md](../SECURITY.md).
- No swarm, no visual world model, no bundled LoRA trainer.
- Quality tracks the local model. A 0.8B tag will burn iterations; a 7B
  tag is a better demo. The gate does not get smarter with scale — the
  policy does.

If a row in the table becomes wrong, open a PR against this file rather
than adding adjectives to the README.
