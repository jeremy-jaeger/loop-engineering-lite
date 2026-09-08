# Examples

| Path | What it is |
| --- | --- |
| [prompts/starter.md](prompts/starter.md) | Copy-paste tasks that fit this harness |
| [offline_vfs_demo.py](offline_vfs_demo.py) | VFS + tools with **no** Ollama |
| [benchmarks.py](benchmarks.py) | Live model scorecard (`--dry-run` lists tasks) |
| [sample_transcript.md](sample_transcript.md) | What a good log looks like |
| [artifacts/](artifacts/) | Files a live TDD run actually produced |

## Gallery (from README)

```bash
agent-loop "Create a User class with __init__, to_dict, and tests in user.py"
agent-loop "Move validation logic from main.py to validator.py; tests must pass"
agent-loop "Build a todo CLI: main.py, models.py, commands.py. Tests must pass."
```

```bash
# No model needed
python3 examples/offline_vfs_demo.py
python3 examples/benchmarks.py --dry-run
```

## Artifacts

`artifacts/` is not the product. It is evidence: palindrome helper, Fibonacci,
Temperature, a Stack — the sort of tiny TDD jobs `scripts/generate_dataset.sh`
feeds the loop. Quality varies (that is the point of verification).

Do not import these modules as a library.
