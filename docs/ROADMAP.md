# Roadmap

What ships today is in the [README](../README.md) and [architecture](architecture.md).
This file is the near-term checklist — not the [north star](NORTH_STAR.md).

## Next

- [ ] Multi-directory VFS UX (keys already support nested paths; `list_files` is still flat)
- [ ] Stronger verification signals (coverage thresholds, optional type checking)
- [ ] OpenAI-compatible chat adapters beyond Ollama’s `/api/chat` shape
- [ ] Retrieval over `knowledge.json` before the prompt bloats

## Later

- [ ] Fine-tuning harness helpers (adapter export docs + scripts; trainer stays external)
- [ ] Swarm mode (spawn N agents, score, merge)
- [ ] Benchmark leaderboard format for local model scorecards
- [ ] Trace replay viewer (optional local dashboard over `dataset.jsonl`)
- [ ] Video / action world-model extension (research track)

## Not planned

- Web UI as the primary interface (keep the CLI first)
- Cloud-hosted inference as a product surface (local-first)
- Shipping a container runtime inside this repo (run *this* tool inside a VM/container instead)

## Already available

- VFS sandbox + verified commit
- Ollama JSON schema loop + `--model` / `--llm-api-base` CLI flags
- Heuristic reflection → `knowledge.json` + JSONL export
- Offline unit tests and `examples/offline_vfs_demo.py`
- CI on Python 3.9 / 3.11 / 3.12
