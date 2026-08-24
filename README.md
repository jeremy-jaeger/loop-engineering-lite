# Loop Engineering Lite

A local coding agent that **simulates** file and shell actions in a virtual
filesystem, then writes to disk **only after pytest or unittest passes**.

That is the whole product. It is small on purpose.

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-14b8a6.svg" alt="MIT License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9%2B-38bdf8.svg" alt="Python 3.9+"></a>
  <a href="https://github.com/jeremy-jaeger/loop-engineering-lite/actions/workflows/ci.yml"><img src="https://github.com/jeremy-jaeger/loop-engineering-lite/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/deps-stdlib%20only-a78bfa.svg" alt="No runtime pip dependencies">
  <img src="https://img.shields.io/badge/inference-Ollama-f59e0b.svg" alt="Ollama">
</p>

[Get started](docs/getting-started.md) ·
[Use cases](docs/use-cases.md) ·
[Comparison](docs/comparison.md) ·
[Failure cases](docs/case-studies/README.md) ·
[Architecture](docs/architecture.md) ·
[Contributing](CONTRIBUTING.md)

---

Most autonomous coding agents talk to your real disk on every tool call.
This one does not.

1. A local Ollama model must emit **strict JSON** (thought, tool, status).
2. File and shell actions apply to an in-memory **virtual file system**.
3. The VFS is materialized in a **tempdir**; the command is scored `1.0` or `0.0`.
4. Host files are written **only after** the last command is a passing
   pytest/unittest run (not after the model says `complete`, not after
   `python3 hello.py` prints, not after three turns have elapsed).
5. Verified traces go to `dataset.jsonl` (`reward=1.0`). Aborts go to
   `data/rejected.jsonl` (`reward=0.0`). Optional heuristics land in
   `knowledge.json`.

The [north star](docs/NORTH_STAR.md) is larger. These two documents stay
separate on purpose.

## Loop contract

| Rule | Behavior |
| --- | --- |
| Unverified `complete` | Retry, then abort. No disk write. |
| Failed tests | `[SIMULATION FAILED]`. No disk write. |
| Generic command exit 0 | Not enough. Last command must be a test run. |
| Inference / JSON error | Retry. Never treated as success. |
| Path jail | Writes cannot leave `--workspace`. |
| Commit | Only paths the agent actually wrote. |

Fourteen recorded failures: **[docs/case-studies](docs/case-studies/README.md)**.

<p align="center">
  <img src="docs/assets/architecture.svg" alt="Think, act, verify, commit, learn, export" width="920">
</p>

## Quick start

**You need:** Python 3.9+ and [Ollama](https://ollama.com) with a chat model.

```bash
git clone https://github.com/jeremy-jaeger/loop-engineering-lite.git
cd loop-engineering-lite
ollama pull qwen3.5:0.8b

# Throwaway workspace — a successful commit writes files here
mkdir -p /tmp/lel-demo && cd /tmp/lel-demo
python3 /path/to/loop-engineering-lite/main.py --workspace . \
  "Use TDD to write is_palindrome(s) in str_utils.py. Test racecar, hello, and ''."
```

Set `OLLAMA_MODEL` to change the tag. Tiny models stall; the gate still holds.

Unit tests (no model, no network):

```bash
cd loop-engineering-lite
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
python3 examples/offline_vfs_demo.py
```

Walkthrough: [docs/getting-started.md](docs/getting-started.md).  
When to use this vs Aider / SWE-agent / an IDE: [docs/comparison.md](docs/comparison.md).  
Checkout-form example: [examples/real_world/checkout_money.md](examples/real_world/checkout_money.md).

## Why it exists

| Slogan you have heard | What we actually ship |
| --- | --- |
| World-model runtime | A file/command sandbox with a binary test score |
| Self-improving agent | Prompt-injected heuristics + reward-labeled JSONL |
| Drop-in for any framework | A loop you can read in one sitting |
| Safe coding agent | Not a container. Tempdir + verification gate. Read [SECURITY.md](SECURITY.md) |

## Layout

```text
main.py            CLI
loop.py            iterations, memory slide, verification gate
llm_client.py      Ollama chat + JSON schema + learned rules
tools.py           list / read / write / replace / run
vfs.py             world model (dict → tempdir → maybe disk)
memory.py          knowledge.json + reward-labeled JSONL
knowledge.json     surviving lessons from past runs
docs/              architecture, ADRs, comparison, case studies
examples/          prompts, offline demo, live-run leftovers
scripts/           dataset batch + case-study log capture
tests/             no Ollama required
```

## Tools the model may call

| Tool | Arguments | Effect |
| --- | --- | --- |
| `list_files` | `directory` (ignored; VFS is flat keys) | Keys currently in the sandbox |
| `read_file` | `filepath` | Contents with line numbers |
| `write_file` | `filepath`, `content` | Upsert in VFS only |
| `search_and_replace` | `filepath`, `old_code`, `new_code` | Exact-match edit |
| `run_command` | `command` | Shell in a **temp copy** of the VFS |

Default grounding: `python3` / `python3 -m pytest`. Override the system
prompt in `llm_client.py` if that is wrong for you.

## Self-improvement, without the trenchcoat

On a verified success the loop:

1. Commits agent-touched files to `--workspace`
2. Appends the trace to `dataset.jsonl` with `reward=1.0`
3. Optionally asks a small model for a generalized rule in `knowledge.json`

On abort it appends `reward=0.0` to `data/rejected.jsonl`. Next runs prepend
surviving rules. That is [experience replay into context](docs/self-improvement.md),
not recursive self-improvement of weights. Use
`scripts/generate_dataset.sh` when you want a pile of verified TDD traces.

## Status

**v0.2.0.** The loop contract above is implemented and unit-tested. Live
quality depends on the local model. Fine-tuning, swarm spawn, and a general
video/action world model are [roadmap language](docs/NORTH_STAR.md).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). Bug reports want a prompt and a log.

```bash
python3 -m pytest -q
python3 scripts/capture_case_studies.py --check
```

## Cite

```bibtex
@software{loop_engineering_lite,
  author  = {Jaeger, Jeremy},
  title   = {Loop Engineering Lite},
  year    = {2026},
  url     = {https://github.com/jeremy-jaeger/loop-engineering-lite},
  version = {0.2.0}
}
```

Or use [`CITATION.cff`](CITATION.cff).

## License

[MIT](LICENSE) © 2026 jeremy-jaeger
