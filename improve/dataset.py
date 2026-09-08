"""Prepare reward-gated ShareGPT / DPO files for MLX or PEFT training."""

from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict

from improve import config


def load_jsonl(path):
    if not path or not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _has_tool_use(messages):
    for m in messages or []:
        content = str(m.get("content", ""))
        if "tool_call" in content or (m.get("role") == "assistant" and "write_file" in content):
            return True
    return False


def is_verified_chosen(row):
    if float(row.get("reward", 0.0)) != 1.0:
        return False
    if not row.get("verified_command"):
        return False
    messages = row.get("messages") or []
    if not messages or not _has_tool_use(messages):
        return False
    return True


def is_rejected(row):
    return float(row.get("reward", 1.0)) == 0.0 and bool(row.get("messages"))


def to_sharegpt(row):
    messages = []
    for m in row.get("messages") or []:
        role = m.get("role") or "user"
        if role not in ("user", "assistant", "system"):
            role = "user"
        messages.append({"role": role, "content": str(m.get("content", ""))})
    return {
        "messages": messages,
        "task": row.get("task"),
        "verified_command": row.get("verified_command"),
        "reward": 1.0,
    }


def _task_key(row):
    task = (row.get("task") or "").strip()
    if task:
        return task
    return hashlib.sha256(json.dumps(row.get("messages"), sort_keys=True).encode()).hexdigest()


def build_dpo_pairs(chosen_rows, rejected_rows):
    by_task_chosen = defaultdict(list)
    by_task_rejected = defaultdict(list)
    for row in chosen_rows:
        by_task_chosen[_task_key(row)].append(row)
    for row in rejected_rows:
        by_task_rejected[_task_key(row)].append(row)

    pairs = []
    for task, chosen_list in by_task_chosen.items():
        rejected_list = by_task_rejected.get(task) or []
        if not rejected_list:
            continue
        chosen = chosen_list[-1]
        rejected = rejected_list[-1]
        pairs.append({
            "task": task,
            "prompt": [{"role": "user", "content": task}],
            "chosen": json.dumps(chosen.get("messages") or [], ensure_ascii=False),
            "rejected": json.dumps(rejected.get("messages") or [], ensure_ascii=False),
            "verified_command": chosen.get("verified_command"),
            "reward_chosen": 1.0,
            "reward_rejected": 0.0,
        })
    return pairs


def split_by_task(rows, valid_fraction=None):
    if valid_fraction is None:
        valid_fraction = config.VALID_FRACTION
    tasks = sorted({_task_key(r) for r in rows})
    n_valid = max(1, int(round(len(tasks) * valid_fraction))) if len(tasks) > 1 else 0
    valid_tasks = set(tasks[:n_valid])
    train, valid = [], []
    for row in rows:
        (valid if _task_key(row) in valid_tasks else train).append(row)
    if not train:
        train, valid = rows, []
    return train, valid


def prepare(chosen_path=None, rejected_path=None, out_dir=None):
    chosen_path = chosen_path or config.CHOSEN_FILE
    rejected_path = rejected_path or config.REJECTED_FILE
    out_dir = out_dir or config.PREPARED_DIR
    os.makedirs(out_dir, exist_ok=True)

    raw_chosen = load_jsonl(chosen_path)
    raw_rejected = load_jsonl(rejected_path)
    chosen = [to_sharegpt(r) for r in raw_chosen if is_verified_chosen(r)]
    rejected = [r for r in raw_rejected if is_rejected(r)]

    if len(chosen) < config.MIN_CHOSEN_TRACES:
        raise ValueError(
            f"Refusing to prepare a training set: found {len(chosen)} verified "
            f"(reward=1.0 + verified_command) traces in {chosen_path}."
        )

    train, valid = split_by_task(chosen)
    pairs = build_dpo_pairs(chosen, rejected)

    write_jsonl(os.path.join(out_dir, "train.jsonl"), train)
    write_jsonl(os.path.join(out_dir, "valid.jsonl"), valid)
    write_jsonl(os.path.join(out_dir, "dpo.jsonl"), pairs)

    summary = {
        "chosen_raw": len(raw_chosen),
        "chosen_verified": len(chosen),
        "rejected": len(rejected),
        "train": len(train),
        "valid": len(valid),
        "dpo_pairs": len(pairs),
        "out_dir": out_dir,
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[PREPARE] {summary}")
    return summary
