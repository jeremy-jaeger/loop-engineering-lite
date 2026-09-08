# Self-improvement (what actually happens)

After a task is **verified complete** (last command is a passing pytest/unittest),
`loop.py` does three things in order:

1. **`vfs.commit_to_reality()`** — write agent-touched paths to disk (blocked if unverified).
2. **`export_trajectory_jsonl(...)`** — append `{messages, reward, task, verified_command}`
   to `dataset.jsonl` (`reward=1.0`). Failures go to `data/rejected.jsonl`.
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

`scripts/generate_dataset.sh` is the data flywheel for step 1. Then:

```bash
python3 -m improve prepare --chosen dataset.jsonl --rejected data/rejected.jsonl
python3 -m improve train && python3 -m improve eval && python3 -m improve promote
```

MLX LoRA runs on Apple Silicon. Elsewhere `train` writes `adapters/train_spec.json`
and does not pretend weights moved.

## `knowledge.json`

Seeded examples in the repo show the intended shape: a task string and a
short generalized rule. Edit or delete the file anytime; an empty or missing
file is valid.
