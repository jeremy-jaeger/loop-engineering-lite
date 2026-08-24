# Getting started

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) installed and running (`http://localhost:11434`)
- A chat model tag. Default: `qwen3.5:0.8b` (small, swarm-friendly).
  Any Ollama chat model that honors JSON `format` works via `--model`.

No pip packages are required to **run** the agent. `pytest` is only for unit tests / the editable install’s `dev` extra.

## Install (recommended)

```bash
# 1. Install Ollama → https://ollama.com
# 2. Pull a model
ollama pull qwen3.5:0.8b

# 3. Clone & editable install (exposes `agent-loop`)
git clone https://github.com/jeremy-jaeger/loop-engineering-lite.git
cd loop-engineering-lite
python3 -m pip install -e ".[dev]"

# 4. Harness tests — no Ollama, no GPU, no network
python3 -m pytest -q
python3 examples/offline_vfs_demo.py
```

## First run (safe)

> **Warning:** `commit_to_reality` writes every file in the VFS into the
> process working directory. Start in a throwaway folder.

```bash
mkdir -p /tmp/lel-demo && cd /tmp/lel-demo
agent-loop "Use TDD to write is_palindrome(s) in str_utils.py. Tests for racecar, hello, and empty string."
```

Equivalent without the console script:

```bash
python3 /path/to/loop-engineering-lite/main.py \
  "Use TDD to write is_palindrome(s) in str_utils.py. Tests for racecar, hello, and empty string."
```

You should see iteration logs, a `[SIMULATION VERIFIED SUCCESS]` or failure
from pytest, then either a commit + optional reflection, or an abort at
`max_iterations`.

### Useful flags

```bash
agent-loop --model qwen2:0.5b --max-iters 15 "…"
agent-loop --llm-api-base http://localhost:11434 "…"
```

`--llm-api-base` defaults to Ollama’s origin. The client calls `{base}/api/chat`.

## Multi-file tasks

The VFS stores files as path-string keys (`models.py`, `pkg/util.py`). Nested
directories are created when simulating or committing. Agents can orchestrate
across multiple files in one prompt:

```bash
agent-loop "Build a todo CLI: main.py (entry), models.py (data), commands.py (actions). Tests must pass."
```

Limitation: `list_files` returns a **flat** key list (no per-directory filter yet).
See [ROADMAP.md](ROADMAP.md).

## Next reading

- [SECURITY.md](../SECURITY.md) — what is / is not sandboxed  
- [examples/prompts/starter.md](../examples/prompts/starter.md) — more tasks  
- [self-improvement.md](self-improvement.md) — `knowledge.json` / JSONL  
- [architecture.md](architecture.md) — loop wiring  
- [COMPARISONS.md](COMPARISONS.md) — vs Genie / LangChain / etc.
