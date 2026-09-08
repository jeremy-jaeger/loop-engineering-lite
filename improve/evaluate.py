"""Held-out TDD suite. Success is VFS pytest/unittest only — never model self-grade."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

from improve import config
from loop import run_agent_loop

HELD_OUT_TASKS = [
    {
        "id": "clamp",
        "prompt": (
            "Use TDD. Write tests in 'test_clamp.py' and implementation in 'clamp.py'. "
            "clamp(x, lo, hi) returns x limited to [lo, hi]. Test x below lo, inside, and above hi."
        ),
    },
    {
        "id": "unique",
        "prompt": (
            "Use TDD. Write tests in 'test_unique.py' and implementation in 'unique.py'. "
            "unique(seq) returns a list of first-seen items preserving order. "
            "Test [1,1,2,2,3] -> [1,2,3] and an empty list."
        ),
    },
    {
        "id": "anagram",
        "prompt": (
            "Use TDD. Write tests in 'test_anagram.py' and implementation in 'anagram.py'. "
            "is_anagram(a, b) is True iff a and b use the same letters ignoring case and spaces. "
            "Test 'listen'/'silent', 'Hello'/'olelh', and a negative case."
        ),
    },
]


def run_suite(call_model=None, tasks=None, enable_reflection=False, max_iterations=8):
    tasks = tasks or HELD_OUT_TASKS
    results = []
    for task in tasks:
        workspace = tempfile.mkdtemp(prefix=f"eval_{task['id']}_")
        outcome = run_agent_loop(
            task["prompt"],
            max_iterations=max_iterations,
            workspace=workspace,
            call_model=call_model,
            enable_reflection=enable_reflection,
        )
        results.append({
            "id": task["id"],
            "success": outcome is not None,
            "workspace": workspace,
        })
    wins = sum(1 for r in results if r["success"])
    report = {
        "wins": wins,
        "n": len(results),
        "win_rate": (wins / len(results)) if results else 0.0,
        "results": results,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    os.makedirs(config.ADAPTERS_DIR, exist_ok=True)
    with open(config.EVAL_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[EVAL] win_rate={report['win_rate']:.2f} ({wins}/{len(results)}) -> {config.EVAL_FILE}")
    return report
