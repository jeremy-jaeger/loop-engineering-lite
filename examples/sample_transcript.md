# Sample transcript

This is the **shape** of a verified palindrome TDD run. Your model and
seed will differ; the gate should not: think → tool → observation →
pytest → commit.

```text
=== Starting local agent loop ===

[START] Agent initialized with prompt:
> Use TDD to write is_palindrome in str_utils.py ...

[WORLD MODEL] Virtual File System loaded. Reality is sandboxed.

--- Iteration 1 ---
[REASONING]
Write tests first so the implementation has a spec.
[ACTION] Calling tool 'write_file' with args: {'filepath': 'test_str_utils.py', ...}

--- Iteration 2 ---
[ACTION] Calling tool 'write_file' with args: {'filepath': 'str_utils.py', ...}

--- Iteration 3 ---
[ACTION] Calling tool 'run_command' with args: {'command': 'python3 -m pytest -q'}
[OBSERVATION]
[SIMULATION VERIFIED SUCCESS]

3 passed in 0.05s

[SUCCESS - TASK COMPLETE]
[VFS COMMIT] Writing agent-touched files back to disk...
[VFS COMMIT] 2 file(s) written.
[DATASET EXPORT] chosen / verified trajectory saved to dataset.jsonl (reward=1.0).
```

If you instead see `[HARNESS INTERVENTION] Refusing unverified completion`,
the model tried to finish without a green test run. That is the product
working. Recorded failures: [docs/case-studies](../docs/case-studies/README.md).
