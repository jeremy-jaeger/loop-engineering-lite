# Use cases

The harness is good at a narrow job: **write a small Python module, prove
it with pytest, then land the files**. The cases below are ones we would
actually run. The ones after that are ones we would not.

## Use it for this

### 1. High-stakes helpers with a crisp spec

Money, slugs, filename sanitizers, retry/backoff, datetime parsing. The
spec fits in a dozen tests. A wrong commit is expensive. The VFS keeps
the wrong draft off disk.

Walkthrough: [examples/real_world/checkout_money.md](../examples/real_world/checkout_money.md).

```bash
mkdir -p /tmp/lel-checkout && cd /tmp/lel-checkout
python3 /path/to/loop-engineering-lite/main.py --workspace . --no-reflect \
  "Use TDD to write dollars_to_cents(text) in money.py. Accept '\$12.34',
   '12.34', and '10'. Return int cents. Raise ValueError for negatives,
   empty strings, or malformed input. Tests in test_money.py. python3 -m pytest -q."
```

Prefer a capable local chat model (`OLLAMA_MODEL=qwen2.5:7b` or similar).
The default tiny tag may stall; the harness will still refuse to commit.

### 2. Teaching how agent loops fail

The [case studies](case-studies/README.md) are the curriculum: lazy
complete, failed tests, path jail, escaped newlines, pytest collection.
Fork `loop.py` in a class and change the gate if you want to show why it
exists.

### 3. Collecting verified traces for fine-tuning

Successful loops append `{messages, reward: 1.0, verified_command}` to
`dataset.jsonl`. Aborts go to `data/rejected.jsonl` with `reward: 0.0`.
That is an honest chosen/rejected pair. `scripts/generate_dataset.sh`
batches TDD prompts. Training itself is not vendored — keep this repo
stdlib-small and train with MLX / axolotl / whatever you already use.

### 4. Evaluating local models on a binary verifier

Same prompt, different `OLLAMA_MODEL`. Success is “pytest passed and
files appeared,” not a judge model. Use `--workspace` per trial so runs
cannot clobber each other.

### 5. Air-gapped or no-cloud machines

Once Ollama and weights are local, the loop does not call a vendor API.
Unit tests do not need Ollama at all.

## Do not use it for this

- **Editing this repository in place.** `commit_to_reality` writes
  touched files into `--workspace`. Run demos from an empty directory.
- **Multi-hour refactors, web apps, or “fix this GitHub issue.”** There
  is no git tool, no browser, no PR reviewer. Use Aider / SWE-agent /
  your IDE.
- **Proof of program correctness.** Case 14 in the case studies:
  `int(float("1.15") * 100) == 114`. Weak tests pass; the code is still
  wrong.
- **Untrusted multi-tenant isolation.** Tempdir is not gVisor. See
  [SECURITY.md](../SECURITY.md).
- **Anything whose success signal is not a test command.** If you cannot
  write pytest, the gate has nothing to check.

## Prompt shape that works

Be explicit about files, tests, and the verifier:

```text
Use TDD.
Write tests in test_<name>.py using def test_... functions (not bare asserts,
not if __name__ == '__main__').
Write the implementation in <name>.py.
Run python3 -m pytest -q and do not mark complete until it passes.
```

Starter copy-paste: [examples/prompts/starter.md](../examples/prompts/starter.md).
