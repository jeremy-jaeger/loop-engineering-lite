# Self-improvement (what actually happens)

## How it works

After a task is **verified complete** (last command is a passing pytest/unittest),
`loop.py` does three things in order:

1. **`vfs.commit_to_reality()`** — write agent-touched paths to disk (blocked if unverified).
2. **`export_trajectory_jsonl(...)`** — append `{messages, reward, task, verified_command}`
   to `dataset.jsonl` (`reward=1.0`). Failures go to `data/rejected.jsonl`.
3. **`reflect_on_trace(...)`** — a second Ollama call that may append a
   `{ "task", "lesson" }` object to `knowledge.json`.
4. **Batch / train (optional)** — use `scripts/generate_dataset.sh` and
   `python3 -m improve …` when you want LoRA / SFT / DPO data.

```text
verified complete
   → commit_to_reality()                 # agent-touched paths only
   → export_trajectory_jsonl(... reward=1.0)  # dataset.jsonl
   → reflect_on_trace(...)               # may append knowledge.json
abort / unverified
   → export_trajectory_jsonl(... reward=0.0)  # data/rejected.jsonl
next run
   → load_knowledge() prepended into call_ollama system prompt
   → resolve_ollama_model() may prefer adapters/current.json
```

That is **experience replay into the prompt**, plus a dataset you can feed to
LoRA later. It is not weight self-modification in-process, and it will bloat the
system prompt until someone adds retrieval ([ROADMAP](ROADMAP.md)).

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

## Fine-tune path

1. Keep only traces with `reward == 1.0` / `[SIMULATION VERIFIED SUCCESS]`.
2. Prepare + train + eval + promote:

```bash
python3 -m improve prepare --chosen dataset.jsonl --rejected data/rejected.jsonl
python3 -m improve train && python3 -m improve eval && python3 -m improve promote
```

3. Promoted adapters are read via `adapters/current.json` on the next
   `call_ollama` (unless you pass an explicit `--model`).

MLX LoRA runs on Apple Silicon. Elsewhere `train` writes `adapters/train_spec.json`
and does not pretend weights moved. `scripts/generate_dataset.sh` remains the
batch data flywheel for step 1.
