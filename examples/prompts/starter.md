# Starter prompts

Run from an **empty working directory**. Quote the whole task. Prefer
`--workspace .` so the destination is obvious.

## Tiny TDD (best fit)

```text
Use TDD to write a Python function is_palindrome(s) in str_utils.py.
Write tests in test_str_utils.py for 'racecar', 'hello', and an empty string.
Use def test_... functions. Run python3 -m pytest -q.
Do not mark complete until tests pass.
```

```text
Use TDD to write fibonacci(n) in math_utils.py.
fib(0)=0, fib(1)=1, fib(10)=55. Raise ValueError for negatives.
Tests in test_math_utils.py. python3 -m pytest -q.
```

```text
Use TDD to build a Stack class in stack.py using a list.
Implement push, pop, and peek. Popping empty raises IndexError.
Keep tests in test_stack.py and instantiate Stack() in every test.
python3 -m pytest -q.
```

## High-stakes helper

```text
Use TDD to write dollars_to_cents(text) in money.py for a checkout form.
Accept '$12.34', '12.34', and '10'. Return int cents.
Raise ValueError for negatives, empty strings, or malformed input.
Include a test for '1.15' -> 115 (watch float rounding).
Tests in test_money.py. python3 -m pytest -q.
```

See [real_world/checkout_money.md](../real_world/checkout_money.md).

## Harness-oriented

```text
Create hello.py that prints Hello, loop. Then run python3 hello.py.
You still must add tests and run python3 -m pytest -q before complete.
```

## Dataset generation

See `scripts/generate_dataset.sh` for a batch of similar TDD jobs used to
fill `data/train.jsonl`.
