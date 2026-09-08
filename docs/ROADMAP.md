# Roadmap

What ships today is in the [README](../README.md) and [architecture](architecture.md).
This file is the near-term checklist — not the [north star](NORTH_STAR.md).

## Next

- [ ] Multi-directory VFS UX (keys already support nested paths; `list_files` is still flat)
- [ ] Stronger verification signals beyond pytest/unittest (coverage thresholds, optional type checking)
- [ ] OpenAI-compatible chat adapters beyond Ollama’s `/api/chat` shape
- [ ] Retrieval over `knowledge.json` before the prompt bloats

## Later

- [ ] Swarm mode (spawn N agents, score, merge)
- [ ] Benchmark leaderboard format for local model scorecards
- [ ] Trace replay viewer (optional local dashboard over `dataset.jsonl`)
- [ ] Video / action world-model extension (research track)

## Not planned

- Web UI as the primary interface (keep the CLI first)
- Cloud-hosted inference as a product surface (local-first)
- Shipping a container runtime inside this repo (run *this* tool inside a VM/container instead)

## Already available

- VFS sandbox + **verification-gated** commit (ADR-006)
- Verifier-guided Best-of-N over VFS forks (`search_width`, ADR-007)
- Adapter flywheel `python3 -m improve prepare|train|eval|promote` (ADR-005; MLX on Apple Silicon)
- Ollama JSON schema loop + `--model` / `--max-iters` / `--llm-api-base` CLI flags
- Heuristic reflection → `knowledge.json` + rewarded JSONL export
- Offline unit tests, ADR regression tests, and `examples/offline_vfs_demo.py`
- CI on Python 3.9 / 3.11 / 3.12
