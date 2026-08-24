<p align="center">
  <img src="docs/assets/banner.jpg" alt="Loop Engineering Lite" width="920">
</p>

# Loop Engineering Lite

**Verify agents before they touch your disk.**

A tiny local harness that forces models to plan and test in a **sandbox**
before committing changes. No cloud, no containers — pure Python + [Ollama](https://ollama.com).

Other agents call tools on your real filesystem. This one **simulates in a
temp copy** and only commits if tests (or the command) actually passed.

```text
Think → Simulate → Commit (only on success)
```

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-14b8a6.svg" alt="MIT License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9%2B-38bdf8.svg" alt="Python 3.9+"></a>
  <a href=".github/workflows/ci.yml"><img src="https://github.com/jeremy-jaeger/loop-engineering-lite/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/deps-stdlib%20only-a78bfa.svg" alt="No runtime pip dependencies">
  <img src="https://img.shields.io/badge/inference-Ollama-f59e0b.svg" alt="Ollama">
  <a href="docs/ROADMAP.md"><img src="https://img.shields.io/badge/status-alpha%200.1.0-64748b.svg" alt="Alpha"></a>
</p>

<p align="center">
  <a href="#first-run-safe">First run</a> ·
  <a href="SECURITY.md">⚠️ Security model</a> ·
  <a href="#examples">Examples</a> ·
  <a href="docs/getting-started.md">Manual</a> ·
  <a href="docs/ROADMAP.md">Roadmap</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

---

## The problem

You want agents that code. You do **not** want them mutating your filesystem
on hallucinations.

| Without Loop | With Loop |
| --- | --- |
| Agent writes to your real `/src` | Agent writes to a temp copy first |
| Bad output overwrites your code | Bad output discarded; good output committed |
| You debug in your actual codebase | You review clean commits with test proof |

**Loop Engineering Lite** is a ~500-line Python harness that:

1. Forces a local model to speak **strict JSON** (thought, tool, status).
2. Applies file and shell actions to an in-memory **virtual file system**.
3. Materializes that VFS in a **tempdir**, runs the command, scores `1.0` / `0.0`.
4. Writes to your machine **only after** a successful simulation (or verified complete).
5. Optionally **remembers** a heuristic in `knowledge.json` and **exports** the trace as JSONL for fine-tuning.

That is the product. The [north star](docs/NORTH_STAR.md) is larger — we keep those separate on purpose.

## See it

<!-- pulse:start -->
<p align="center">
  <a href="docs/pulse.md"><img src="docs/assets/pulse.svg" alt="Live repository pulse redrawn by CI from GitHub stars, forks, and contributors" width="920"></a>
</p>

<p align="center"><sub>CI last redrew this README 2026-08-24 07:43 UTC. Live totals: 0 stars, 0 forks, 0 watchers, 2 open issues/PRs, 1 listed contributors (<code>jeremy-jaeger</code>). History just started — this is sample zero of the sparkline. The particle field and sparkline are generated from those numbers (<a href="scripts/generate_pulse.py">how</a>).</sub></p>
<!-- pulse:end -->

<p align="center">
  <img src="docs/assets/terminal-demo.svg" alt="Example terminal session of a verified TDD loop" width="920">
</p>

## Install

```bash
# 1. Install Ollama first → https://ollama.com
# 2. Pull a small model
ollama pull qwen3.5:0.8b   # default in code; qwen2:0.5b also works

# 3. Clone & install this repo
git clone https://github.com/jeremy-jaeger/loop-engineering-lite.git
cd loop-engineering-lite
python3 -m pip install -e ".[dev]"

# 4. Confirm harness works without a model (zero cloud, zero GPU)
python3 -m pytest -q
python3 examples/offline_vfs_demo.py
```

## First Run (Safe)

> **This writes files to your working directory** on a successful commit.
> Always start in a throwaway folder.

```bash
mkdir -p /tmp/lel-demo && cd /tmp/lel-demo
agent-loop "Use TDD to write is_palindrome(s) in str_utils.py. Test racecar, hello, and ''."
```

Or without the console script:

```bash
python3 /path/to/loop-engineering-lite/main.py \
  "Use TDD to write is_palindrome(s) in str_utils.py. Test racecar, hello, and ''."
```

Then check `/tmp/lel-demo/` for committed files.

CLI flags:

```bash
agent-loop --help
agent-loop --model qwen2:0.5b --max-iters 15 "…"
agent-loop --llm-api-base http://localhost:11434 "…"
```

Full walkthrough: **[docs/getting-started.md](docs/getting-started.md)**.

## Why Loop

| Framework | Disk safety | Offline | Self-improve | Weight |
| --- | --- | --- | --- | --- |
| LangChain agents | ❌ by default | ❌ (usually) | ❌ | Large |
| AutoGPT-style | ❌ by default | ❌ (usually) | ❌ | Heavy |
| **Loop Lite** | ✅ VFS + verify | ✅ Ollama only | ✅ JSONL + heuristics | Tiny |

- **Disk safety** — sandbox first; commit only when the simulation scores success.
- **Offline** — no API key, no cloud inference; just local Ollama (or a compatible base URL).
- **Self-improving** — trajectory → heuristic in `knowledge.json` → prompt injection; export for LoRA.
- **Lightweight** — stdlib runtime, runs on sub-2B models.

See also [docs/COMPARISONS.md](docs/COMPARISONS.md) (Genie / JEPA / Dreamer / LangChain).

## Examples

### Generate a small module with tests

```bash
agent-loop "Create a User class with __init__, to_dict, and tests in user.py"
```

### Refactor with verification

```bash
agent-loop "Move validation logic from main.py to validator.py; tests must pass"
```

### Multi-file workflow

Agents can orchestrate **many files** in one run. VFS keys are path strings
(e.g. `pkg/models.py`); nested dirs are created on simulate/commit.
`list_files` is flat (no directory walk filter yet) — see [ROADMAP](docs/ROADMAP.md).

```bash
agent-loop "Build a todo CLI: main.py (entry), models.py (data), commands.py (actions). Tests must pass."
```

More copy-paste tasks → [examples/prompts/starter.md](examples/prompts/starter.md).  
Offline VFS walkthrough → [examples/offline_vfs_demo.py](examples/offline_vfs_demo.py).  
Simple model scorecard → [examples/benchmarks.py](examples/benchmarks.py).

## Security model

**Not a container.** Tempdir + commit. A malicious or jailbroken model prompt
can still escape the tempdir via shell tricks.

| Protects against | Does **not** protect against |
| --- | --- |
| Accidental host mutation while the model is still failing | Prompt injection / code injection |
| Shipping broken edits without a passing command | Escaping `shell=True` in the tempdir |
| Overwriting good code with an unverified hallucination | Running untrusted models on a host you care about |

**Recommended:** run untrusted models inside a VM or container. Details →
**[SECURITY.md](SECURITY.md)**.

## Self-improvement (concrete)

After a successful run the loop:

1. Saves the trace to `dataset.jsonl`.
2. Asks a small model to distill a heuristic.
3. Stores that rule in `knowledge.json` and prepends it on future prompts.
4. Lets you batch traces with `scripts/generate_dataset.sh` for LoRA.

```json
[
  {
    "task": "…",
    "lesson": "Always run tests before marking complete"
  }
]
```

Full flow → [docs/self-improvement.md](docs/self-improvement.md).

## Layout

```text
main.py            CLI (argparse → agent-loop)
loop.py            iterations, memory slide, interventions
llm_client.py      Ollama chat + schema + learned rules
tools.py           list / read / write / replace / run
vfs.py             world model (dict → tempdir → maybe disk)
memory.py          knowledge.json + dataset.jsonl
docs/              getting started, architecture, roadmap, comparisons
examples/          prompts, offline demo, benchmarks
tests/             stdlib / pytest — no model required
```

## Tools the model may call

| Tool | Arguments | Effect |
| --- | --- | --- |
| `list_files` | `directory` (ignored; flat key listing) | Keys currently in the sandbox |
| `read_file` | `filepath` | Contents with line numbers |
| `write_file` | `filepath`, `content` | Upsert in VFS only |
| `search_and_replace` | `filepath`, `old_code`, `new_code` | Exact-match edit |
| `run_command` | `command` | Shell in a **temp copy** of the VFS |

## Docs map

1. **What is it?** — this README  
2. **Quick start** — [getting-started.md](docs/getting-started.md)  
3. **Manual** — tools, VFS guarantees, [FAQ](docs/faq.md), [SECURITY.md](SECURITY.md)  
4. **Examples** — [examples/](examples/)  
5. **Deep dive** — [architecture](docs/architecture.md), [ADRs](docs/adr/), [NORTH_STAR](docs/NORTH_STAR.md), [ROADMAP](docs/ROADMAP.md)

## Status

**v0.1.0 alpha.** Loop, VFS, tools, truncation, reflection, and export are
real and unit-tested. Live quality depends on the local model. See
[ROADMAP.md](docs/ROADMAP.md) for what is next vs not planned.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). Bug reports want a prompt, model, and
log — see [issue templates](.github/ISSUE_TEMPLATE/).

```bash
python3 -m pytest -q
```

## Cite

```bibtex
@software{loop_engineering_lite,
  author = {Jaeger, Jeremy},
  title  = {Loop Engineering Lite},
  year   = {2026},
  url    = {https://github.com/jeremy-jaeger/loop-engineering-lite},
  version = {0.1.0}
}
```

Or use [`CITATION.cff`](CITATION.cff).

## License

[MIT](LICENSE) © 2026 jeremy-jaeger
