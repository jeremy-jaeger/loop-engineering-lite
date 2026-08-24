# Starter prompts

Run from an **empty working directory**. Quote the whole task.

## Real-world (CMS slug)

```text
Use TDD to write slugify(text) in slugify.py for a CMS URL helper.
Rules: lowercase; spaces and underscores become hyphens; keep only
letters, digits, and hyphens; collapse repeated hyphens; strip leading
and trailing hyphens. Empty or punctuation-only input returns ''.
Write tests in test_slugify.py for: 'Hello, World!' -> 'hello-world',
'  API_v2 Release  ' -> 'api-v2-release', '---' -> ''.
Use python3 -m pytest. Do not mark complete until tests pass.
```

Full write-up: [real_world/cms_slugify.md](../real_world/cms_slugify.md).

## Tiny TDD (best fit)

```text
Use TDD to write a Python function is_palindrome(s) in str_utils.py.
Write tests for 'racecar', 'hello', and an empty string. Use python3 -m pytest.
```

```text
Use TDD to write fibonacci(n) in math_utils.py.
fib(0)=0, fib(1)=1, fib(10)=55. Raise ValueError for negatives.
```

```text
Use TDD to build a Stack class in stack.py using a list.
Implement push, pop, and peek. Popping empty raises IndexError.
Keep tests in test_stack.py and instantiate Stack() in every test.
```

## Harness-oriented

```text
Create hello.py that prints Hello, loop. Then run python3 hello.py and
only complete when the command succeeds.
```

```text
List files, read README.md if it exists, and summarize the repo in two sentences.
Do not mark complete until you have used list_files.
```

## Dataset generation

See `scripts/generate_dataset.sh` for a batch of similar TDD jobs used to
fill `data/train.jsonl`.
