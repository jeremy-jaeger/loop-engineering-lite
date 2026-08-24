# Self-improvement (what actually happens)

After a task is **verified**, `loop.py` does three things in order:

1. **`vfs.commit_to_reality()`** — write agent-touched files onto disk.
2. **`export_trajectory_jsonl(..., reward=1.0)`** — append
   `{messages, reward, task, verified_command}` to `dataset.jsonl`.
3. **`reflect_on_trace(...)`** (unless `--no-reflect`) — a second Ollama
   call that may append `{task, lesson}` to `knowledge.json`.

If the loop hits `max_iterations` without verification, it exports
`reward=0.0` to `data/rejected.jsonl` and writes nothing to the host.

The next `call_ollama` prepends surviving lessons as
`CRITICAL PAST LEARNINGS`.

That is **experience replay into the prompt**, plus a dataset you can
feed to LoRA later. It is not weight self-modification, and it will bloat
the system prompt until someone adds retrieval.

## Fine-tune path (manual, not automated here)

ADR-005 sketches:

1. Keep traces with `reward == 1.0` and a `verified_command`.
2. Use `data/rejected.jsonl` as DPO rejected pairs if you want them.
3. Train LoRA (for example with `mlx-lm` on Apple silicon).
4. Fuse / GGUF and point Ollama at the new tag (`OLLAMA_MODEL`).

`scripts/generate_dataset.sh` is the data flywheel for step 1. Training
code is deliberately not vendored so this repo stays stdlib-small.

## `knowledge.json`

Seeded examples in the repo show the intended shape: a task string and a
short generalized rule. Edit or delete the file anytime; an empty or
missing file is valid.
