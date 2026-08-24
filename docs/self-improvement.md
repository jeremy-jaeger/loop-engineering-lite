# Self-improvement (what actually happens)

After a task is marked complete, `loop.py` does three things in order:

1. **`vfs.commit_to_reality()`** — dump the in-memory file map onto disk.
2. **`export_trajectory_jsonl(messages)`** — append ShareGPT-style
   `{ "messages": [...] }` to `dataset.jsonl`.
3. **`reflect_on_trace(...)`** — a second Ollama call that may append a
   `{ "task", "lesson" }` object to `knowledge.json`.

The next `call_ollama` prepends those lessons as `CRITICAL PAST LEARNINGS`.

That is **experience replay into the prompt**, plus a dataset you can feed to
LoRA later. It is not weight self-modification, and it will bloat the system
prompt until someone adds retrieval.

## Fine-tune path (manual, not automated here)

ADR-005 sketches:

1. Keep only traces that ended in `[SIMULATION VERIFIED SUCCESS]`.
2. Train LoRA (for example with `mlx-lm` on Apple silicon).
3. Fuse / GGUF and point Ollama at the new tag.

`scripts/generate_dataset.sh` is the data flywheel for step 1. Training code
is deliberately not vendored so this repo stays stdlib-small.

## `knowledge.json`

Seeded examples in the repo show the intended shape: a task string and a
short generalized rule. Edit or delete the file anytime; an empty or missing
file is valid.
