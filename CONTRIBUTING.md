# Contributing

The bar is **small, verified, local**.

## Before you write code

1. Read [docs/NORTH_STAR.md](docs/NORTH_STAR.md) so you know what we are not claiming.
2. Skim [docs/architecture.md](docs/architecture.md), [docs/comparison.md](docs/comparison.md),
   and the ADRs in [docs/adr/](docs/adr/).
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
python3 -m pytest -q
python3 scripts/capture_case_studies.py --check
python3 examples/offline_vfs_demo.py
```

You **do** need [Ollama](https://ollama.com) for a live loop:

```bash
ollama pull qwen3.5:0.8b
python3 main.py --workspace /tmp/lel-demo --no-reflect \
  "Use TDD to write is_palindrome in str_utils.py"
```

Always pass `--workspace` (or `cd`) to an empty directory so
`commit_to_reality` cannot overwrite this repo.

## What we want

- Harness interventions that catch real model failure modes
- New case studies with logs when you find a new failure
- Tests that do not require a GPU or a network model
- Honest docs when a feature is aspirational vs implemented

## What we will bounce

- Framework rewrites that add a stack without a verification story
- Prompt-only “self-improvement” with no artifact or test
- Drive-by dependency explosions (the runtime is stdlib + Ollama on purpose)
- Vanity metrics in the README (stars, pulses, generated hero art)

## Style

- Python 3.9+, stdlib first
- No unused imports
- Name the failure mode in comments, not the personality of the agent

## Pull requests

- One concern per PR
- Update examples or docs when user-visible behavior changes
- Fill in the PR template test plan
- Do not include editor-vendor badges, agent footers, or generated
  “open in …” chips

By contributing, you agree that your work is licensed under the MIT License.
