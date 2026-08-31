#!/usr/bin/env python3
"""
Simple local model scorecard.

Runs each prompt through the live agent loop (requires Ollama) and prints
pass/fail. Useful for "my qwen2:0.5b got 2/5" posts.

Usage:
  python3 examples/benchmarks.py
  python3 examples/benchmarks.py --model qwen2:0.5b --max-iters 12
  python3 examples/benchmarks.py --dry-run   # print tasks only (no Ollama)
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BENCHMARKS = [
    (
        "palindrome",
        "Use TDD to write is_palindrome(s) in str_utils.py. "
        "Tests for 'racecar', 'hello', and empty string. Use python3 -m pytest.",
    ),
    (
        "fizzbuzz",
        "Use TDD to write fizzbuzz(n) in fizzbuzz.py returning the classic list "
        "for 1..n. Cover n=15. Use python3 -m pytest.",
    ),
    (
        "fibonacci",
        "Use TDD to write fibonacci(n) in math_utils.py. "
        "fib(0)=0, fib(1)=1, fib(10)=55. Raise ValueError for negatives.",
    ),
    (
        "stack",
        "Use TDD to build a Stack class in stack.py using a list. "
        "Implement push, pop, peek. Popping empty raises IndexError. "
        "Keep tests in test_stack.py.",
    ),
    (
        "todo_cli_multifile",
        "Build a tiny todo CLI across main.py, models.py, and commands.py. "
        "Include pytest tests that must pass before complete.",
    ),
]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Loop Engineering Lite benchmark suite")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--max-iters", type=int, default=10)
    parser.add_argument("--llm-api-base", default="http://localhost:11434")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List benchmark prompts without calling Ollama",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        for name, prompt in BENCHMARKS:
            print(f"## {name}\n{prompt}\n")
        print(f"{len(BENCHMARKS)} tasks (dry-run)")
        return 0

    from loop import run_agent_loop

    results = []
    for name, prompt in BENCHMARKS:
        print(f"\n======== BENCHMARK: {name} ========\n")
        with tempfile.TemporaryDirectory(prefix=f"lel_bench_{name}_") as td:
            prev = os.getcwd()
            os.chdir(td)
            try:
                answer = run_agent_loop(
                    initial_prompt=prompt,
                    max_iterations=args.max_iters,
                    model=args.model,
                    llm_api_base=args.llm_api_base,
                )
                passed = answer is not None
            finally:
                os.chdir(prev)
        results.append((name, passed))
        print(f"[BENCH] {name}: {'PASS' if passed else 'FAIL'}")

    passed_n = sum(1 for _, ok in results if ok)
    print("\n======== SCORECARD ========")
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n{passed_n}/{len(results)} on model={args.model}")
    return 0 if passed_n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
