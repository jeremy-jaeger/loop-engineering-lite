"""LoRA / DPO trainer: MLX on Apple Silicon, plan file otherwise."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from improve import config
from improve.dataset import prepare


def detect_backend():
    try:
        import mlx.core  # noqa: F401
        import mlx_lm  # noqa: F401
        return "mlx"
    except Exception:
        pass
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        import peft  # noqa: F401
        return "peft"
    except Exception:
        return "plan"


def _mlx_train_cmd(data_dir, adapter_dir, base_model, iters):
    return [
        sys.executable, "-m", "mlx_lm", "lora",
        "--model", base_model,
        "--data", data_dir,
        "--adapter-path", adapter_dir,
        "--iters", str(iters),
        "--batch-size", "1",
        "--num-layers", "8",
        "--max-seq-length", "2048",
    ]


def _mlx_fuse_cmd(base_model, adapter_dir, fused_dir):
    return [
        sys.executable, "-m", "mlx_lm", "fuse",
        "--model", base_model,
        "--adapter-path", adapter_dir,
        "--save-path", fused_dir,
    ]


def _write_spec(spec):
    os.makedirs(config.ADAPTERS_DIR, exist_ok=True)
    with open(config.TRAIN_SPEC_FILE, "w") as f:
        json.dump(spec, f, indent=2)
    return config.TRAIN_SPEC_FILE


def train(
    chosen_path=None,
    rejected_path=None,
    out_dir=None,
    adapter_dir=None,
    base_model=None,
    iters=200,
    backend=None,
    plan_only=False,
):
    summary = prepare(chosen_path=chosen_path, rejected_path=rejected_path, out_dir=out_dir)
    backend = backend or detect_backend()
    if plan_only:
        backend = "plan"
    base_model = base_model or config.DEFAULT_BASE_MODEL
    adapter_dir = adapter_dir or os.path.join(config.ADAPTERS_DIR, "lora")
    fused_dir = os.path.join(config.ADAPTERS_DIR, "fused")
    data_dir = summary["out_dir"]

    spec = {
        "backend": backend,
        "base_model": base_model,
        "ollama_model": config.DEFAULT_OLLAMA_MODEL,
        "adapter_dir": adapter_dir,
        "fused_dir": fused_dir,
        "data_dir": data_dir,
        "iters": iters,
        "chosen_verified": summary["chosen_verified"],
        "dpo_pairs": summary["dpo_pairs"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "planned",
        "mlx_train": _mlx_train_cmd(data_dir, adapter_dir, base_model, iters),
        "mlx_fuse": _mlx_fuse_cmd(base_model, adapter_dir, fused_dir),
    }

    if backend == "plan":
        spec["status"] = "plan_only"
        _write_spec(spec)
        print(f"[TRAIN] No MLX/PEFT backend (or --plan-only). Spec -> {config.TRAIN_SPEC_FILE}")
        print("[TRAIN] On Apple Silicon: pip install mlx mlx-lm && python3 -m improve train")
        return spec

    os.makedirs(adapter_dir, exist_ok=True)
    if backend == "mlx":
        cmd = spec["mlx_train"]
        print("[TRAIN] Running:", " ".join(cmd))
        result = subprocess.run(cmd, check=False)
        spec["returncode"] = result.returncode
        spec["status"] = "trained" if result.returncode == 0 else "train_failed"
        if result.returncode == 0:
            fuse = spec["mlx_fuse"]
            print("[TRAIN] Fusing:", " ".join(fuse))
            fused = subprocess.run(fuse, check=False)
            spec["fuse_returncode"] = fused.returncode
            spec["status"] = "fused" if fused.returncode == 0 else "trained_unfused"
        _write_spec(spec)
        return spec

    spec["status"] = "peft_not_inlined"
    spec["peft_notes"] = (
        "PEFT is installed but this repo does not vendor a CUDA loop. "
        "SFTTrainer on data/mlx/train.jsonl with LoRA r=8 against the Qwen 0.8B class, "
        "then export GGUF. Reward filtering already ran."
    )
    _write_spec(spec)
    print("[TRAIN] PEFT detected; filtered data at", data_dir)
    return spec
