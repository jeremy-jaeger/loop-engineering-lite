# Self-improvement (what actually happens)

## How it works

1. **After a successful run**, the loop saves the message trace to `dataset.jsonl`.
2. **Extraction**: a small Ollama model distills the trajectory into one generalized heuristic (or `NO_NEW_RULE`).
3. **Injection**: that rule is appended to `knowledge.json` and prepended to future system prompts as `CRITICAL PAST LEARNINGS`.
4. **Export**: batch verified traces with `scripts/generate_dataset.sh` when you want LoRA / SFT data.

```text
run succeeds
   → commit_to_reality()
   → export_trajectory_jsonl(messages)   # dataset.jsonl
   → reflect_on_trace(...)               # may append knowledge.json
next run
   → load_knowledge() prepended into call_ollama system prompt
```

That is **experience replay into the prompt**, plus a dataset you can feed to
LoRA later. It is not weight self-modification, and it will bloat the system
prompt until someone adds retrieval ([ROADMAP](ROADMAP.md)).

## Example `knowledge.json`

```json
[
  {
    "task": "Use TDD to write is_palindrome(s)…",
    "lesson": "Always run tests before marking complete"
  },
  {
    "task": "Refactor validator into its own module…",
    "lesson": "If pytest fails, read the error line number before editing again"
  }
]
```

Edit or delete the file anytime; an empty or missing file is valid.

## Fine-tune path (manual, not automated here)

ADR-005 sketches:

1. Keep only traces that ended in `[SIMULATION VERIFIED SUCCESS]`.
2. Train LoRA (for example with `mlx-lm` on Apple silicon).
3. Fuse / GGUF and point Ollama at the new tag.

`scripts/generate_dataset.sh` is the data flywheel for step 1. Training code
is deliberately not vendored so this repo stays stdlib-small.
