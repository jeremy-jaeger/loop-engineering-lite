import os

DEFAULT_OLLAMA_MODEL = "qwen3.5:0.8b"
DEFAULT_BASE_MODEL = os.environ.get("LOOP_BASE_MODEL", "Qwen/Qwen3-0.8B")

CHOSEN_FILE = "dataset.jsonl"
REJECTED_FILE = os.path.join("data", "rejected.jsonl")
PREPARED_DIR = os.path.join("data", "mlx")
ADAPTERS_DIR = "adapters"
CURRENT_ADAPTER = os.path.join(ADAPTERS_DIR, "current.json")
EVAL_FILE = os.path.join(ADAPTERS_DIR, "last_eval.json")
BASELINE_FILE = os.path.join(ADAPTERS_DIR, "baseline.json")
TRAIN_SPEC_FILE = os.path.join(ADAPTERS_DIR, "train_spec.json")

PROMOTE_DELTA = 0.05
MIN_CHOSEN_TRACES = 1
VALID_FRACTION = 0.1

# Aliases so train/eval/promote/tests share one vocabulary
DEFAULT_OLLAMA_MODEL = DEFAULT_OLLAMA_MODEL
DEFAULT_BASE_MODEL = DEFAULT_BASE_MODEL
DEFAULT_OLLAMA_MODEL = DEFAULT_OLLAMA_MODEL
DEFAULT_BASE_MODEL = DEFAULT_BASE_MODEL
CURRENT_ADAPTER = CURRENT_ADAPTER
TRAIN_SPEC_FILE = TRAIN_SPEC_FILE
