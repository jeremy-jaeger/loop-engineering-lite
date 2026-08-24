"""Loop contract: no commit, no chosen export, without a passing test run."""
import json
import os
import tempfile
import unittest

import memory
from loop import run_agent_loop
from llm_client import inference_error

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

ZERO_TESTS = """print('I am not a pytest module')
"""


def scripted(responses):
    queue = list(responses)

    def _call(_messages):
        if not queue:
            return {"status": "in_progress", "thought_process": "stall"}
        return queue.pop(0)

    return _call


class LoopGateTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.workspace = self.td.name
        self.chosen = os.path.join(self.td.name, "chosen.jsonl")
        self.rejected = os.path.join(self.td.name, "rejected.jsonl")
        self._orig_chosen = memory.DATASET_FILE
        self._orig_rejected = memory.REJECTED_FILE
        memory.DATASET_FILE = self.chosen
        memory.REJECTED_FILE = self.rejected

    def tearDown(self):
        memory.DATASET_FILE = self._orig_chosen
        memory.REJECTED_FILE = self._orig_rejected
        self.td.cleanup()

    def _load_jsonl(self, path):
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_immediate_complete_does_not_commit_or_export_success(self):
        result = run_agent_loop(
            "do a task",
            max_iterations=2,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [
                    {"status": "complete", "thought_process": "done", "final_answer": "ok"},
                    {"status": "complete", "thought_process": "done", "final_answer": "ok"},
                ]
            ),
        )
        self.assertIsNone(result)
        self.assertEqual(self._load_jsonl(self.chosen), [])
        rejected = self._load_jsonl(self.rejected)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reward"], 0.0)
        self.assertEqual(rejected[0]["task"], "do a task")

    def test_len_messages_is_not_a_success_signal(self):
        result = run_agent_loop(
            "do a task",
            max_iterations=1,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [{"status": "complete", "thought_process": "lazy", "final_answer": ""}]
            ),
        )
        self.assertIsNone(result)
        self.assertEqual(self._load_jsonl(self.chosen), [])

    def test_failed_tests_export_rejected_and_do_not_commit(self):
        result = run_agent_loop(
            "write tests",
            max_iterations=3,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [
                    {
                        "status": "in_progress",
                        "thought_process": "write failing test",
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
                        "thought_process": "run tests",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m unittest test_ok.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "claim success",
                        "final_answer": "all green",
                    },
                ]
            ),
        )
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(os.path.join(self.workspace, "test_ok.py")))
        self.assertEqual(self._load_jsonl(self.chosen), [])
        rejected = self._load_jsonl(self.rejected)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["reward"], 0.0)

    def test_passing_unittest_commits_touched_files_and_exports_reward(self):
        result = run_agent_loop(
            "write passing tests",
            max_iterations=4,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [
                    {
                        "status": "in_progress",
                        "thought_process": "write test",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "test_ok.py",
                                "content": PASSING_UNITTEST,
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "run tests",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m unittest test_ok.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "verified",
                        "final_answer": "",
                    },
                ]
            ),
        )
        self.assertEqual(result, "Task successfully completed and verified by VFS.")
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "test_ok.py")))
        chosen = self._load_jsonl(self.chosen)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["reward"], 1.0)
        self.assertEqual(chosen[0]["task"], "write passing tests")
        self.assertIn("unittest", chosen[0]["verified_command"])
        self.assertEqual(self._load_jsonl(self.rejected), [])

    def test_print_script_success_does_not_unlock_commit(self):
        result = run_agent_loop(
            "print hello",
            max_iterations=3,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [
                    {
                        "status": "in_progress",
                        "thought_process": "write",
                        "tool_call": {
                            "name": "write_file",
                            "args": {
                                "filepath": "hello.py",
                                "content": "print('hello')\n",
                            },
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "run",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 hello.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "it printed",
                        "final_answer": "done",
                    },
                ]
            ),
        )
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(os.path.join(self.workspace, "hello.py")))

    def test_inference_error_does_not_commit(self):
        result = run_agent_loop(
            "do a task",
            max_iterations=2,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [inference_error("connection refused"), inference_error("still down")]
            ),
        )
        self.assertIsNone(result)
        self.assertEqual(self._load_jsonl(self.chosen), [])
        self.assertEqual(len(self._load_jsonl(self.rejected)), 1)

    def test_zero_collected_tests_do_not_verify(self):
        result = run_agent_loop(
            "write tests",
            max_iterations=3,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [
                    {
                        "status": "in_progress",
                        "thought_process": "write a script, not tests",
                        "tool_call": {
                            "name": "write_file",
                            "args": {"filepath": "test_ok.py", "content": ZERO_TESTS},
                        },
                    },
                    {
                        "status": "in_progress",
                        "thought_process": "run pytest",
                        "tool_call": {
                            "name": "run_command",
                            "args": {"command": "python3 -m pytest -q test_ok.py"},
                        },
                    },
                    {
                        "status": "complete",
                        "thought_process": "pytest ran",
                        "final_answer": "done",
                    },
                ]
            ),
        )
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(os.path.join(self.workspace, "test_ok.py")))

    def test_missing_tool_call_retries(self):
        result = run_agent_loop(
            "do a task",
            max_iterations=1,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted(
                [{"status": "in_progress", "thought_process": "thinking aloud"}]
            ),
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
