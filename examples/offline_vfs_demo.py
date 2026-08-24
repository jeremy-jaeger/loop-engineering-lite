#!/usr/bin/env python3
"""World-model demo with no LLM.

Shows the contract the agent sees: mutate VFS, simulate a command, commit
only if the score is 1.0.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import execute_tool  # noqa: E402
from vfs import VirtualFileSystem  # noqa: E402


def main() -> int:
    work = tempfile.mkdtemp(prefix="lel_offline_")
    vfs = VirtualFileSystem(base_dir=work)

    execute_tool(
        vfs,
        "write_file",
        {
            "filepath": "str_utils.py",
            "content": (
                "def is_palindrome(s: str) -> bool:\n"
                "    return s == s[::-1]\n"
            ),
        },
    )
    execute_tool(
        vfs,
        "write_file",
        {
            "filepath": "test_str_utils.py",
            "content": (
                "from str_utils import is_palindrome\n"
                "def test_cases():\n"
                "    assert is_palindrome('racecar')\n"
                "    assert not is_palindrome('hello')\n"
                "    assert is_palindrome('')\n"
            ),
        },
    )

    observation = execute_tool(
        vfs, "run_command", {"command": "python3 -m pytest -q test_str_utils.py"}
    )
    print(observation)
    print("list_files:\n", execute_tool(vfs, "list_files", {}))

    if "[SIMULATION VERIFIED SUCCESS]" not in observation:
        print("Sandbox tests failed; not committing.", file=sys.stderr)
        return 1

    vfs.commit_to_reality()
    print(f"Committed into {work}")
    print("Host files:", os.listdir(work))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
