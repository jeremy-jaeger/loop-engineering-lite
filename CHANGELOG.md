# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- CLI via `argparse`: `--model`, `--max-iters`, `--llm-api-base`
- README rewrite: verify-before-commit headline, before/after table, Why Loop, examples gallery
- `docs/ROADMAP.md`, `docs/COMPARISONS.md`; stronger `SECURITY.md` isolation table
- `examples/benchmarks.py` (live scorecard + `--dry-run`)
- CI coverage report on Python 3.12; richer bug report template fields

### Changed

- Getting-started flow leads with editable install + throwaway-dir warning
- Self-improvement docs spell out the four-step knowledge/JSONL flow

## [0.1.0] — 2026-08-24

### Added

- Local ReAct-style loop over Ollama with a strict JSON response schema
- Virtual file system sandbox: simulate edits and commands, commit only after success
- Tool adapters: `list_files`, `read_file`, `write_file`, `search_and_replace`, `run_command`
- Sliding-window memory and observation truncation for small-context models
- Reflection pass that appends heuristics to `knowledge.json`
- ShareGPT-style trajectory export to `dataset.jsonl`
- Batch TDD dataset generator (`scripts/generate_dataset.sh`)
- Public-repo docs, examples, diagrams, and stdlib unit tests
- Self-updating pulse: CI redraws generative art, appends daily star history, and patches README.md between `pulse:` markers

### Known limits

- Live inference requires a local Ollama daemon (or compatible `--llm-api-base`)
- `commit_to_reality` writes the full VFS snapshot back to the working directory
- Fine-tuning (MLX / LoRA) is a documented pipeline, not a bundled trainer
- Tempdir isolation is not a container — see SECURITY.md
