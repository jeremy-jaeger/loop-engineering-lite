# loop-engineering-lite

A local ReAct harness for sub-2B models: VFS world model, binary test verification, then weight updates only from traces that actually passed.

## Loop
```
python3 main.py "Use TDD to write clamp(x, lo, hi) with tests."
```

Unverified `complete` does not write the host disk and does not enter SFT data (ADR-006).

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
python3 -m unittest test_adr006 test_adr005 -v
```
