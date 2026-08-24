#!/usr/bin/env python3
"""CLI for the verification-gated local agent loop."""
import argparse
import sys

from loop import run_agent_loop


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run a local coding agent that simulates file and shell actions "
            "in a virtual filesystem and commits only after tests pass."
        )
    )
    parser.add_argument(
        "prompt",
        nargs="+",
        help='Task for the agent, e.g. "Use TDD to write is_palindrome in str_utils.py"',
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Directory to load into the VFS and (if verified) commit into. Default: cwd.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum think-act turns before aborting (default: 10).",
    )
    parser.add_argument(
        "--no-reflect",
        action="store_true",
        help="Skip the post-success reflection pass that may append to knowledge.json.",
    )
    return parser


def cli_entry(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    user_prompt = " ".join(args.prompt)

    print("=== Starting local agent loop ===")
    final_result = run_agent_loop(
        initial_prompt=user_prompt,
        max_iterations=args.max_iterations,
        workspace=args.workspace,
        enable_reflection=not args.no_reflect,
    )
    print("\n=== Execution Complete ===")
    if final_result:
        print(f"Final Output: {final_result}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(cli_entry())
