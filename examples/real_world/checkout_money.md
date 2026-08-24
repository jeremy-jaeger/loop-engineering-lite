# Real-world use: checkout money parser

## The problem

A checkout form sends dollar strings like `$12.34` or `0.99`. The payment
API wants **integer cents**. A buggy converter that drops a decimal or
accepts negatives charges the wrong amount.

| Input | Expected cents |
| --- | --- |
| `$12.34` | `1234` |
| `0.99` | `99` |
| `10` | `1000` |

You want a local coding agent to write the helper **and prove it with tests**
before anything lands on disk.

## Why this loop fits

1. Writes `money.py` + `test_money.py` inside an in-memory VFS.
2. Runs `python3 -m pytest` in a temp copy of that VFS.
3. Commits **only after** pytest succeeds.
4. Leaves disk untouched when the simulation fails.

That is a verified micro-PR for a small, high-stakes utility.

## Prompt (empty working directory)

```bash
mkdir -p /tmp/lel-checkout && cd /tmp/lel-checkout

python3 /path/to/loop-engineering-lite/main.py --workspace . --no-reflect \
  "Use TDD to write dollars_to_cents(text) in money.py for a checkout form.
Accept '\$12.34', '12.34', and '10'. Return int cents (1234, 1234, 1000).
Raise ValueError for negatives, empty strings, or malformed input.
Write tests in test_money.py using from money import dollars_to_cents
and def test_... functions. Use python3 -m pytest -q.
Do not mark complete until tests pass."
```

Set `OLLAMA_MODEL` to a capable chat tag (for example `qwen2.5:7b`).
The default tiny model may stall; the harness still refuses unverified
commits.

## What success looks like

- Log contains `[SIMULATION VERIFIED SUCCESS]` from pytest
- Then `[VFS COMMIT]` / `[SUCCESS - TASK COMPLETE]`
- `money.py` and `test_money.py` exist in the workspace
- Re-running `python3 -m pytest -q` in that directory still passes

## What success does not mean

`examples/artifacts/money.py` is a live-run leftover that uses
`int(float(text) * 100)`. `int(float("1.15") * 100) == 114`. If the
model's tests never mention `1.15`, pytest stays green. The gate is
only as strong as the spec you put in the prompt. See
[case study 14](../../docs/case-studies/README.md).
