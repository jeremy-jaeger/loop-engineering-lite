#!/usr/bin/env python3
"""Record harness logs for the published failure case studies.

Each case is a scripted model (no Ollama). The logs are the real loop
stdout for that failure mode. Paths are normalized so CI can --check them.

    python3 scripts/capture_case_studies.py
    python3 scripts/capture_case_studies.py --check
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import memory  # noqa: E402
from llm_client import inference_error  # noqa: E402
from loop import run_agent_loop  # noqa: E402
from tools import execute_tool  # noqa: E402
from vfs import VirtualFileSystem  # noqa: E402

LOG_DIR = ROOT / "docs" / "case-studies" / "logs"

PASSING_UNITTEST = """import unittest

class SmokeTest(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(True)
"""

FAILING_UNITTEST = """import unittest

class SmokeTest(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(False)
"""

ZERO_TESTS = "print('I am not a pytest module')\n"


def scripted(responses):
    queue = list(responses)

    def _call(_messages):
        if not queue:
            return {"status": "in_progress", "thought_process": "stall"}
        return queue.pop(0)

    return _call


def normalize(text, workspace):
    text = text.replace(workspace, "$WORKSPACE")
    text = text.replace(str(ROOT), "$REPO")
    text = re.sub(r"/tmp/agent_sim_[A-Za-z0-9_]+", "$SIM", text)
    return text


def capture_loop(prompt, responses, max_iterations, workspace):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_agent_loop(
            prompt,
            max_iterations=max_iterations,
            workspace=workspace,
            enable_reflection=False,
            call_model=scripted(responses),
        )
    return buf.getvalue()


def write_tool(workspace, name, args):
    vfs = VirtualFileSystem(base_dir=workspace)
    buf = io.StringIO()
    with redirect_stdout(buf):
        obs = execute_tool(vfs, name, args)
        print(obs)
        if name == "write_file":
            path = args.get("filepath", "")
            print("host_exists:", os.path.exists(os.path.join(workspace, path)))
            if path in vfs.state:
                print("vfs_repr:", repr(vfs.state[path]))
        print("commit:", vfs.commit_to_reality())
        print("verified:", vfs.is_task_verified())
    return buf.getvalue()


def cases(workspace):
    return [
        (
            "01-unverified-complete",
            capture_loop(
                "Use TDD to write is_palindrome in str_utils.py",
                [
                    {
                        "status": "complete",
                        "thought_process": "I already know how palindromes work.",
                        "final_answer": "Done. str_utils.py is correct.",
                    }
                ]
                * 3,
                3,
                workspace,
            ),
        ),
        (
            "02-message-count-is-not-success",
            capture_loop(
                "Build a Stack class",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "I will write a file.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "stack.py",
                                "content": "class Stack:\n    pass\n",
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "I will write another file to look busy.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "notes.txt",
                                "content": "looks like progress\n",
                            },
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "Several turns have elapsed, so this must be done.",
                        "final_answer": "",
                    },
                ],
                3,
                workspace,
            ),
        ),
        (
            "03-failed-tests-blocked",
            capture_loop(
                "Write tests for a passing smoke check",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Write a failing test.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "test_ok.py",
                                "content": FAILING_UNITTEST,
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "Run tests.",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m unittest test_ok.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "I ran the tests, so I am done.",
                        "final_answer": "all green",
                    },
                ],
                3,
                workspace,
            ),
        ),
        (
            "04-print-is-not-verification",
            capture_loop(
                "Create hello.py that prints Hello",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Write the script.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "hello.py",
                                "content": "print('Hello')\n",
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "Run it.",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 hello.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "It printed. Simulation succeeded.",
                        "final_answer": "hello.py works",
                    },
                ],
                3,
                workspace,
            ),
        ),
        (
            "05-path-jail",
            write_tool(workspace, "write_file", {"filepath": "../escape.py", "content": "pwned\n"}),
        ),
        (
            "06-inference-error",
            capture_loop(
                "Use TDD to write clamp(x, lo, hi)",
                [inference_error("HTTP Error 500: Internal Server Error")] * 2,
                2,
                workspace,
            ),
        ),
        (
            "07-search-and-replace-miss",
            capture_loop(
                "Fix off-by-one in math_utils.py",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Write a file.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "math_utils.py",
                                "content": "def add(a, b):\n    return a + b\n",
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "Patch with a guessed indent.",
                        "tool_call": {
                            "name": "search_and_replace",
                            "args": {
                                "filepath": "math_utils.py",
                                "old_code": "def add(a,b):",
                                "new_code": "def add(a, b):",
                            },
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "Eh, close enough.",
                        "final_answer": "patched",
                    },
                ],
                3,
                workspace,
            ),
        ),
        (
            "08-escaped-newlines",
            write_tool(
                workspace,
                "write_file",
                {
                    "filepath": "str_utils.py",
                    "content": "def is_palindrome(s):\\n    return s == s[::-1]\\n",
                },
            ),
        ),
        (
            "09-zero-tests-collected",
            capture_loop(
                "Use TDD. Tests in test_pal.py, implementation in pal.py",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Write a script named like a test file.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {"filepath": "test_pal.py", "content": ZERO_TESTS},
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "Run pytest.",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m pytest -q test_pal.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "pytest ran.",
                        "final_answer": "tested",
                    },
                ],
                3,
                workspace,
            ),
        ),
        (
            "10-command-timeout",
            capture_loop(
                "Run a long command",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Sleep too long.",
                        "tool_call": {
                            "name": "run_command",
                            "args": {
                                "command": "python3 -c 'import time; time.sleep(30)'",
                            },
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "It ran.",
                        "final_answer": "ok",
                    },
                ],
                2,
                workspace,
            ),
        ),
        (
            "11-abort-exports-rejected",
            capture_loop(
                "Write a validated email helper",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Stall without a tool.",
                    }
                ],
                1,
                workspace,
            ),
        ),
        (
            "12-tests-live-in-implementation",
            capture_loop(
                "Use TDD to write is_palindrome in str_utils.py with pytest",
                [
                    {
                        "status": "in_progress",
                        "thought_process": "Put tests under if __name__ in the impl file.",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "str_utils.py",
                                "content": (
                                    "def is_palindrome(s):\n"
                                    "    return s == s[::-1]\n\n"
                                    "if __name__ == '__main__':\n"
                                    "    assert is_palindrome('racecar')\n"
                                    "    print('ok')\n"
                                ),
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "Run pytest on the implementation file.",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m pytest -q str_utils.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "The file ran.",
                        "final_answer": "tests passed",
                    },
                ],
                3,
                workspace,
            ),
        ),
    ]


def render(workspace):
    orig_chosen = memory.DATASET_FILE
    orig_rejected = memory.REJECTED_FILE
    memory.DATASET_FILE = os.path.join(workspace, "dataset.jsonl")
    memory.REJECTED_FILE = os.path.join(workspace, "rejected.jsonl")
    try:
        rendered = {}
        for name, body in cases(workspace):
            rendered[name] = normalize(body, workspace)
        return rendered
    finally:
        memory.DATASET_FILE = orig_chosen
        memory.REJECTED_FILE = orig_rejected


def write_logs(rendered):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in rendered.items():
        (LOG_DIR / f"{name}.log").write_text(body, encoding="utf-8")
        print(f"wrote {name}.log ({len(body.splitlines())} lines)")


def check_logs(rendered):
    missing = []
    mismatched = []
    for name, body in rendered.items():
        path = LOG_DIR / f"{name}.log"
        if not path.exists():
            missing.append(name)
            continue
        existing = path.read_text(encoding="utf-8")
        if existing != body:
            mismatched.append(name)
    if missing or mismatched:
        print("Case-study logs are out of date.")
        if missing:
            print("missing:", ", ".join(missing))
        if mismatched:
            print("mismatched:", ", ".join(mismatched))
        print("Re-run: python3 scripts/capture_case_studies.py")
        return 1
    print(f"{len(rendered)} case-study logs match.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    td = tempfile.TemporaryDirectory(prefix="lel_cases_")
    os.environ["LEL_SIM_TIMEOUT"] = os.environ.get("LEL_SIM_TIMEOUT", "1")
    try:
        rendered = render(td.name)
    finally:
        td.cleanup()
    if args.check:
        return check_logs(rendered)
    write_logs(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
