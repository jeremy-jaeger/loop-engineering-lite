# Getting started

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) running locally (`http://localhost:11434`)
- A chat model tag. The default in code is `qwen3.5:0.8b` (small, swarm-friendly).
  Any Ollama chat model that honors JSON `format` will work if you change the
  `model=` argument.

No pip packages are required to **run** the agent. `pytest` is only for unit tests.

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

`commit_to_reality` writes every file in the VFS back into the process working
directory. Do not discover that the hard way on this repo.

```bash
mkdir -p /tmp/lel-demo && cd /tmp/lel-demo
python3 /path/to/loop-engineering-lite/main.py \
  "Use TDD to write is_palindrome(s) in str_utils.py. Tests for racecar, hello, and empty string."
```

You should see iteration logs, a `[SIMULATION VERIFIED SUCCESS]` or failure
from pytest, then either a commit + optional reflection, or an abort at
`max_iterations`.

## CLI

```bash
python3 main.py "Build a Temperature class in temp.py with Celsius in, Fahrenheit out."
# or, after pip install -e .
agent-loop "List files, then summarize what this folder contains."
```

Arguments are joined into one prompt. Default cap is 10 iterations
(`run_agent_loop(..., max_iterations=10)`).

## Without a model

The VFS and tools are ordinary Python. Unit tests cover them:

```bash
cd loop-engineering-lite
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

There is also a no-Ollama walkthrough in
[examples/offline_vfs_demo.py](../examples/offline_vfs_demo.py).

## Batch trajectories

From the **repository root**:

```bash
chmod +x scripts/generate_dataset.sh
./scripts/generate_dataset.sh
```

Successful `dataset.jsonl` files are appended to `data/train.jsonl`. That
script runs live models and **will write files into the current directory**.
Use a throwaway workspace if you do not want artifacts in git.

## Environment notes

The system prompt currently tells the model it is on **macOS** and to use
`python3` / `python3 -m pytest`. On Linux that still works. If you need
Windows, you will want to relax that grounding string in `llm_client.py`.
