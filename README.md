# loop-engineering-lite

A local ReAct harness for sub-2B models: VFS world model, binary test verification, then weight updates only from traces that actually passed.

## Loop
```
python3 main.py "Use TDD to write clamp(x, lo, hi) with tests."
python3 -c "from loop import run_agent_loop; run_agent_loop('...', search_width=3, verify_command='python3 -m pytest -q')"
```

Unverified `complete` does not write the host disk (ADR-006). `search_width>1` forks the VFS, scores candidates with tests, and keeps the winner (ADR-007).

## Weight flywheel (ADR-005)
```
./generate_dataset.sh
python3 -m improve prepare --chosen dataset.jsonl --rejected data/rejected.jsonl
python3 -m improve train          # MLX LoRA on Apple Silicon; otherwise writes adapters/train_spec.json
python3 -m improve eval           # held-out TDD, pytest/unittest only
python3 -m improve promote        # hot-swap only if win_rate beats baseline
```

Promoted tags are read by `llm_client.resolve_ollama_model()`.

## Tests
```
python3 -m unittest test_adr006 test_adr005 test_adr007 -v
```
