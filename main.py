#!/usr/bin/env python3
"""CLI entry for Loop Engineering Lite."""

import argparse
import sys

from loop import run_agent_loop


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent-loop",
        description="Local agent harness with VFS sandbox — verify before commit.",
        epilog='Example: agent-loop "Use TDD to write is_palindrome(s)"',
    )
    parser.add_argument(
        "prompt",
        help="Task description (quote the whole string)",
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=10,
        help="Maximum loop iterations (default: 10)",
    )
    parser.add_argument(
        "--model",
        default="qwen3.5:0.8b",
        help="Ollama (or compatible) model tag (default: qwen3.5:0.8b)",
    )
    parser.add_argument(
        "--llm-api-base",
        default="http://localhost:11434",
        help="LLM HTTP origin (default: http://localhost:11434). Client POSTs to {base}/api/chat",
    )
    return parser


def cli_entry(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_iters < 1:
        parser.error("--max-iters must be >= 1")

    print("=== Starting Lightweight Local Agent ===")
    final_result = run_agent_loop(
        initial_prompt=args.prompt,
        max_iterations=args.max_iters,
        model=args.model,
        llm_api_base=args.llm_api_base,
    )

    print("\n=== Execution Complete ===")
    if final_result:
        print(f"Final Output: {final_result}")
    return 0 if final_result else 1


if __name__ == "__main__":
    sys.exit(cli_entry())
