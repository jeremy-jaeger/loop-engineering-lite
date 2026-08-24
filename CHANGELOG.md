# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-08-24

### Added

- Verification gate (ADR-006): commit and `reward=1.0` export only after a
  passing pytest/unittest (or `test_*.py`) run
- Path jail and commit of agent-touched files only
- Rejected-trace export (`data/rejected.jsonl`, `reward=0.0`)
- Inference errors retry instead of faking `complete`
- Harness nudges for failed `search_and_replace`, failed tests, and zero
  collected tests
- `write_file` normalization for escaped newlines and trailing brace junk
- CLI flags: `--workspace`, `--max-iterations`, `--no-reflect`
- Failure case studies with recorded logs, comparison, and use-case guide
- CI on Python 3.9–3.13, plus a log-replay job

### Changed

- `len(messages) > 3` is no longer a success signal
- System prompt no longer claims the host is macOS
- Status is the loop contract, not an alpha badge

### Removed

- Live repository “pulse” graphic and the CI job that rewrote the README
  from star counts

## [0.1.0] — 2026-08-24

### Added

- Local ReAct-style loop over Ollama with a strict JSON response schema
- Virtual file system sandbox
- Tool adapters: `list_files`, `read_file`, `write_file`, `search_and_replace`, `run_command`
- Sliding-window memory and observation truncation
- Reflection pass that appends heuristics to `knowledge.json`
- ShareGPT-style trajectory export
- Batch TDD dataset generator (`scripts/generate_dataset.sh`)

### Known limits

- Live inference requires a local Ollama daemon
- Fine-tuning (MLX / LoRA) is a documented pipeline, not a bundled trainer
- The verifier is only as strong as the tests the model writes
