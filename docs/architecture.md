# Architecture

This repository is a **small Python harness**, not a training framework.

A local model (via [Ollama](https://ollama.com)) emits **one JSON object per
step**. The harness either runs a tool against an in-memory **virtual file
system**, or it stops. Shell commands never execute on your real tree first:
they run in a tempdir snapshot. Host files are written only when the last
command is a passing pytest/unittest run.

```
User prompt
    → Ollama JSON
        → tools.py
            → VFS sandbox (score 0.0 → back to the model)
            → score 1.0 on a verification command + status complete
                → commit touched files
                → knowledge.json (optional)
                → dataset.jsonl (reward=1.0)
```

Failed or aborted loops append `data/rejected.jsonl` with `reward=0.0`.

## Implemented today

| Piece | Module | Job |
| --- | --- | --- |
| Loop | `loop.py` | Iterations, memory slide, verification gate, tool dispatch |
| Inference | `llm_client.py` | Ollama `/api/chat` + JSON schema + injected lessons |
| World model | `vfs.py` | Dict of files, tempdir rollouts, `fork`/`adopt`, gated commit |
| Tools | `tools.py` | list / read / write / replace / run |
| Memory | `memory.py` | Heuristics + reward-labeled JSONL |
| CLI | `main.py` | `python3 main.py --workspace DIR "…"` |

## Guardrails in the loop

1. **Tool enforcement** — `in_progress` without a `tool_call` is rejected.
2. **Verified complete** — `status: complete` commits only after a passing
   pytest/unittest. `len(messages) > 3` is not a signal.
3. **Inference errors** — HTTP / JSON failures retry; they never complete.
4. **Horizontal truncation** — observations longer than 3k characters keep head + tail.
5. **Vertical compaction** — when the message list exceeds `max_memory_items`,
   keep the original prompt and the last few turns.
6. **Path jail** — writes cannot escape `--workspace`.
7. **Touched-path commit** — substrate files the agent never wrote stay put.

Recorded counterexamples: [case-studies](case-studies/README.md).

## What is not implemented yet

The north star talks about general world models, swarm spawning, and weight
updates. Those are **goals**. The VFS is a compositional file world, not
Dreamer/JEPA. Reflection is heuristic injection, not recursive
self-improvement of weights. See [NORTH_STAR.md](NORTH_STAR.md) and [adr/](adr/).

## File layout

```
main.py                 CLI
loop.py                 runtime
llm_client.py           Ollama + system prompt
tools.py                tool router
vfs.py                  sandbox
memory.py               learn + export
knowledge.json          surviving heuristics
scripts/                dataset batch, case-study capture
examples/               prompts, offline demo, live leftovers
docs/                   this guide, ADRs, comparison, case studies
tests/                  no Ollama
```
