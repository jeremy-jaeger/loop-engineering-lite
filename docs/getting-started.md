# Getting started

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) running locally (`http://localhost:11434`)
- A chat model tag. Default is `qwen3.5:0.8b`. Override with `OLLAMA_MODEL`.
  Any Ollama chat model that honors JSON `format` will work.

No pip packages are required to **run** the agent. `pytest` is only for
this repository's unit tests (the agent still expects `python3 -m pytest`
inside the sandbox for TDD tasks).

## Install

```bash
git clone https://github.com/jeremy-jaeger/loop-engineering-lite.git
cd loop-engineering-lite
ollama pull qwen3.5:0.8b
```

Optional editable install (exposes the `agent-loop` console script):

```bash
python3 -m pip install -e ".[dev]"
```

## First run (safe)

`commit_to_reality` writes agent-touched files into `--workspace` (default:
the current working directory). Do not discover that on this repo.

```bash
mkdir -p /tmp/lel-demo && cd /tmp/lel-demo
python3 /path/to/loop-engineering-lite/main.py --workspace . \
  "Use TDD to write is_palindrome(s) in str_utils.py. Tests for racecar, hello, and empty string."
```

You should see iteration logs, then either:

- `[SIMULATION VERIFIED SUCCESS]` from pytest, then `[VFS COMMIT]`, or
- `[HARNESS INTERVENTION]` / `[ABORT]` if the model never got tests green

Tiny models often abort. That is expected. The gate is doing its job.
Try a larger tag:

```bash
export OLLAMA_MODEL=qwen2.5:7b
```

## CLI

```bash
python3 main.py --workspace /tmp/lel-demo --max-iterations 12 --no-reflect \
  "Use TDD to build a Temperature class in temp.py"
# after pip install -e .
agent-loop --workspace /tmp/lel-demo "List files, then summarize."
```

Arguments after the flags are joined into one prompt.

## Without a model

```bash
cd loop-engineering-lite
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 examples/offline_vfs_demo.py
python3 scripts/capture_case_studies.py --check
```

## Batch trajectories

From the **repository root**:

```bash
chmod +x scripts/generate_dataset.sh
./scripts/generate_dataset.sh
```

Successful `dataset.jsonl` files are appended to `data/train.jsonl`.
Aborted runs land in `data/rejected.jsonl`. The script **will write files
into the current directory** on success — use a throwaway workspace copy
if you do not want artifacts in git.

## Environment notes

The system prompt asks for `python3` and `python3 -m pytest`. That is
correct on macOS and Linux. On Windows you will want to relax the
grounding string in `llm_client.py`.

Next: [use cases](use-cases.md), [comparison](comparison.md),
[failure cases](case-studies/README.md).
