# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-08-24

### Added

- Local ReAct-style loop over Ollama with a strict JSON response schema
- Virtual file system sandbox: simulate edits and commands; commit only after a passing pytest/unittest (ADR-006)
- Test-time Best-of-N over VFS forks (`search_width`, ADR-007)
- Adapter flywheel `python3 -m improve prepare|train|eval|promote` (ADR-005)
- Tool adapters: `list_files`, `read_file`, `write_file`, `search_and_replace`, `run_command`
- Sliding-window memory and observation truncation for small-context models
- Reflection pass that appends heuristics to `knowledge.json`
- ShareGPT-style trajectory export to `dataset.jsonl`
- Batch TDD dataset generator (`scripts/generate_dataset.sh`)
- Public-repo docs, examples, diagrams, and stdlib unit tests
- Self-updating pulse: CI redraws generative art, appends daily star history, and patches README.md between `pulse:` markers

### Known limits

- Live inference requires a local Ollama daemon
- `commit_to_reality` writes only agent-touched paths, and only after verification
- Fine-tuning runs on Apple Silicon via MLX; elsewhere `improve train` writes a plan file instead of fake weights
