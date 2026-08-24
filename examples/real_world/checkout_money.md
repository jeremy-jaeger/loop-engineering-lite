# Real-world use: checkout money parser (verify before commit)

## The problem

You are shipping a small checkout form. The browser sends dollar strings like
`$12.34` or `0.99`. Your payment API wants **integer cents**. A buggy
converter that silently drops the decimal or accepts negatives can charge the
wrong amount.

| Input | Expected cents |
| --- | --- |
| `$12.34` | `1234` |
| `0.99` | `99` |
| `10` | `1000` |

You want a local coding agent to write the helper **and prove it with tests**
before anything lands on disk.

## Why this loop is effective here

Loop Engineering Lite:

1. Writes `money.py` + `test_money.py` inside an in-memory VFS.
2. Runs `python3 -m pytest` in a **temp copy** of that VFS.
3. Commits to your working directory **only after** pytest succeeds.
4. Leaves disk untouched when the simulation fails.

That is the practical pattern: a **verified micro-PR factory** for small,
high-stakes utilities (money, slugs, filename sanitizers, retry helpers).

## Prompt (run from an empty directory)

```bash
mkdir -p /tmp/lel-checkout && cd /tmp/lel-checkout

python3 /path/to/loop-engineering-lite/main.py \
  "Use TDD to write dollars_to_cents(text) in money.py for a checkout form.
Accept '$12.34', '12.34', and '10'. Return int cents (1234, 1234, 1000).
Raise ValueError for negatives, empty strings, or malformed input.
Write tests in test_money.py using from money import dollars_to_cents
and def test_... functions. Use python3 -m pytest -q.
Do not mark complete until tests pass."
```

Prefer a capable local chat model (for example `qwen2.5:7b`) for this task.
The default tiny model may stall; the harness will still refuse to commit
unverified code.

## What success looks like

- Log contains `[SIMULATION VERIFIED SUCCESS]`
- Then `[VFS COMMIT]` / `[SUCCESS - TASK COMPLETE]`
- `/tmp/lel-checkout/money.py` and `test_money.py` exist
- Re-running `python3 -m pytest -q` in that directory still passes
