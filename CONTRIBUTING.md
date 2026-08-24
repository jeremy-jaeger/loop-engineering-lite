# Contributing

Thanks for taking this runtime seriously. The bar is **small, verified, local**.

## Before you write code

1. Read [docs/NORTH_STAR.md](docs/NORTH_STAR.md) so you know what we are *not* claiming.
2. Skim [docs/architecture.md](docs/architecture.md) and the ADRs in [docs/adr/](docs/adr/).
3. Open an issue if the change is more than a docs typo.

## Dev setup

```bash
git clone https://github.com/jeremy-jaeger/loop-engineering-lite.git
cd loop-engineering-lite
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

You do **not** need Ollama for unit tests:

```bash
python -m pytest -q
```

You **do** need [Ollama](https://ollama.com) for a live loop:

```bash
ollama pull qwen3.5:0.8b
python3 main.py "Use TDD to write is_palindrome in /tmp/demo_palindrome.py"
```

Prefer running live demos from an empty directory so `commit_to_reality` cannot overwrite this repo.

## What we want

- Harness interventions that catch real model failure modes
- Stronger sandboxing and clearer verification signals
- Tests that do not require a GPU or a network model
- Honest docs when a feature is aspirational vs implemented

## What we will bounce

- Framework rewrites that add a stack without a verification story
- Prompt-only "self-improvement" with no artifact or test
- Drive-by dependency explosions (the runtime is stdlib + Ollama on purpose)

## Style

- Python 3.9+, stdlib first
- No unused imports
- Name the failure mode in comments, not the personality of the agent

## Pull requests

- One concern per PR
- Update examples or docs when user-visible behavior changes
- Fill in the PR template test plan

By contributing, you agree that your work is licensed under the MIT License.
