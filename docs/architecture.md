# Architecture

Loop Engineering Lite is a **small Python harness**, not a training framework.

A local model (via [Ollama](https://ollama.com)) emits **one JSON object per step**.
The harness either runs a tool against an in-memory **virtual file system**, or it
stops. Shell commands never execute on your real tree first: they run in a
tempdir snapshot. If the process exits 0, the snapshot may be committed.

```mermaid
flowchart LR
  U[User prompt] --> L[Ollama JSON]
  L -->|tool_call| T[tools.py]
  T --> V[VFS sandbox]
  V -->|score 0.0| L
  V -->|score 1.0 + complete| C[commit_to_reality]
  C --> K[knowledge.json]
  C --> D[dataset.jsonl]
```

## Implemented today

| Piece | Module | Job |
| --- | --- | --- |
| Loop | `loop.py` | Iterations, memory slide, lazy-complete retry, tool dispatch |
| Inference | `llm_client.py` | Ollama `/api/chat` + JSON schema + injected lessons |
| World model | `vfs.py` / `world_model.py` | Dict of files, tempdir rollouts, `fork`/`value`, gated commit |
| Search | `search.py` | Best-of-N over forks, scored by pytest/unittest |
| Memory | `memory.py` | Heuristics + reward-labeled JSONL |
| Flywheel | `improve/` | prepare / train / eval / promote |
| CLI | `main.py` | `python3 main.py "…"` |

## Guardrails in the loop

1. **Tool enforcement** — `in_progress` without a `tool_call` is rejected.
2. **Verified complete** — `status: complete` commits only after a passing pytest/unittest. The `len(messages) > 3` shortcut is gone.
3. **Horizontal truncation** — observations longer than 3k characters keep head + tail.
4. **Vertical compaction** — when the message list exceeds `max_memory_items`, keep the original prompt and the last few turns.
5. **Test-time search** — `search_width>1` scores mutating actions on VFS forks before adopting one.

## What is *not* implemented yet

The north star still asks for latent video/action world models, framework
adapters, and process-level swarm spawn. The VFS is a *compositional file
world*, not Dreamer/JEPA. Adapter training exists as `improve/` (MLX on Apple
Silicon; otherwise a plan file). See [NORTH_STAR.md](NORTH_STAR.md) and
[adr/](adr/).

## File layout

```
main.py                 CLI
loop.py                 runtime
llm_client.py           Ollama + system prompt
tools.py                tool router
vfs.py                  sandbox + fork/value
world_model.py          rollout API
search.py               Best-of-N
improve/                prepare / train / eval / promote
memory.py               learn + export
knowledge.json          surviving heuristics
scripts/generate_dataset.sh
examples/               prompts and prior TDD artifacts
docs/                   this guide, ADRs, assets
tests/                  stdlib tests (no Ollama), including ADR-005/006/007
```
