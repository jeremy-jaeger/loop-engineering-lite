"""Hot-swap gate: only promote adapters that beat the held-out baseline."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from improve import config


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def write_modelfile(ollama_from, spec):
    os.makedirs(config.ADAPTERS_DIR, exist_ok=True)
    path = os.path.join(config.ADAPTERS_DIR, "Modelfile")
    fused = spec.get("fused_dir") or os.path.join(config.ADAPTERS_DIR, "fused")
    body = (
        f"FROM {ollama_from}\n"
        f"# After GGUF conversion of {fused}, point FROM at that file.\n"
        "PARAMETER temperature 0\n"
        "PARAMETER num_ctx 4096\n"
    )
    with open(path, "w") as f:
        f.write(body)
    return path


PROMOTABLE_TRAIN_STATUS = {
    "trained",
    "fused",
    "trained_unfused",
    "peft_not_inlined",
}


def promote(eval_path=None, baseline_path=None, min_delta=None, ollama_model=None, allow_baseline=False):
    eval_path = eval_path or config.EVAL_FILE
    baseline_path = baseline_path or config.BASELINE_FILE
    min_delta = config.PROMOTE_DELTA if min_delta is None else min_delta
    report = _load(eval_path)
    if not report:
        raise ValueError(f"No eval report at {eval_path}. Run: python3 -m improve eval")

    baseline = _load(baseline_path, {"win_rate": 0.0, "n": 0})
    delta = float(report["win_rate"]) - float(baseline.get("win_rate", 0.0))
    spec = _load(config.TRAIN_SPEC_FILE, {})
    ollama_model = ollama_model or spec.get("ollama_model") or config.DEFAULT_OLLAMA_MODEL
    status = spec.get("status")

    decision = {
        "promoted": False,
        "reason": "",
        "win_rate": report["win_rate"],
        "baseline_win_rate": baseline.get("win_rate", 0.0),
        "delta": delta,
        "min_delta": min_delta,
        "evaluated_at": report.get("evaluated_at"),
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "ollama_model": ollama_model,
        "backend": spec.get("backend"),
        "adapter_dir": spec.get("adapter_dir"),
        "fused_dir": spec.get("fused_dir"),
        "train_status": status,
    }

    if allow_baseline and baseline.get("n", 0) == 0:
        decision["promoted"] = True
        decision["reason"] = "recording first eval baseline (no prior adapter)"
    elif status not in PROMOTABLE_TRAIN_STATUS:
        decision["reason"] = f"train status {status!r} is not a trained adapter"
    elif delta < min_delta:
        decision["reason"] = (
            f"win_rate {report['win_rate']:.2f} does not beat baseline "
            f"{baseline.get('win_rate', 0.0):.2f} by {min_delta}"
        )
    else:
        decision["promoted"] = True
        decision["reason"] = "held-out win_rate improved past promote delta"

    os.makedirs(config.ADAPTERS_DIR, exist_ok=True)
    if decision["promoted"]:
        with open(config.CURRENT_ADAPTER, "w") as f:
            json.dump(decision, f, indent=2)
        with open(baseline_path, "w") as f:
            json.dump({"win_rate": report["win_rate"], "n": report["n"]}, f, indent=2)
        write_modelfile(ollama_model, spec)
        print(f"[PROMOTE] {decision['reason']} -> {config.CURRENT_ADAPTER}")
    else:
        print(f"[PROMOTE BLOCKED] {decision['reason']}")
        with open(os.path.join(config.ADAPTERS_DIR, "last_promote_block.json"), "w") as f:
            json.dump(decision, f, indent=2)
    return decision
