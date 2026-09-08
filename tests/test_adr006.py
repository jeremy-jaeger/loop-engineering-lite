import json
import os
import tempfile
import unittest

import memory
from loop import run_agent_loop
from vfs import VirtualFileSystem, is_verification_command


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


def scripted(responses):
    queue = list(responses)

    def _call(_messages):
        if not queue:
            return {"status": "in_progress", "thought_process": "stall"}
        return queue.pop(0)

    return _call


class VerificationHelpersTest(unittest.TestCase):
    def test_pytest_and_unittest_are_verification(self):
        self.assertTrue(is_verification_command("python3 -m pytest test_stack.py -q"))
        self.assertTrue(is_verification_command("python3 -m unittest test_ok.py"))
        self.assertTrue(is_verification_command("python3 test_ok.py"))
        self.assertFalse(is_verification_command("python3 main.py"))
        self.assertFalse(is_verification_command("ls -la"))
        self.assertFalse(is_verification_command(""))


class VfsCommitTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.workspace = self.td.name
        with open(os.path.join(self.workspace, "untouched.txt"), "w") as f:
            f.write("host-original")
        self.vfs = VirtualFileSystem(base_dir=self.workspace)

    def tearDown(self):
        self.td.cleanup()

    def test_commit_blocked_without_verification(self):
        self.vfs.write_file("agent.py", "print(1)\n")
        self.assertFalse(self.vfs.commit_to_reality())
        self.assertFalse(os.path.exists(os.path.join(self.workspace, "agent.py")))
        with open(os.path.join(self.workspace, "untouched.txt")) as f:
            self.assertEqual(f.read(), "host-original")

    def test_commit_writes_only_touched_paths(self):
        self.vfs.write_file("agent.py", "print(1)\n")
        self.vfs.record_command("python3 -m unittest test_ok.py", 1.0)
        self.assertTrue(self.vfs.is_task_verified())
        self.assertTrue(self.vfs.commit_to_reality())
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "agent.py")))
        with open(os.path.join(self.workspace, "untouched.txt")) as f:
            self.assertEqual(f.read(), "host-original")

    def test_path_jail(self):
        msg = self.vfs.write_file("../escape.py", "nope")
        self.assertIn("Error", msg)
        self.assertNotIn("../escape.py", self.vfs.state)


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
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_immediate_complete_does_not_commit_or_export_success(self):
        result = run_agent_loop(
            "do a task",
            max_iterations=2,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted([
                {"status": "complete", "thought_process": "done", "final_answer": "ok"},
                {"status": "complete", "thought_process": "done", "final_answer": "ok"},
            ]),
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
            call_model=scripted([
                {
                    "status": "complete",
                    "thought_process": "lazy",
                    "final_answer": "",
                }
            ]),
        )
        self.assertIsNone(result)
        self.assertEqual(self._load_jsonl(self.chosen), [])

    def test_failed_tests_export_rejected_and_do_not_commit(self):
        result = run_agent_loop(
            "write tests",
            max_iterations=3,
            workspace=self.workspace,
            enable_reflection=False,
            call_model=scripted([
                {
                    "status": "in_progress",
                    "thought_process": "write failing test",
                    "tool_call": {
                        "name": "write_file",
                        "args": {"filepath": "test_ok.py", "content": FAILING_UNITTEST},
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
            ]),
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
            call_model=scripted([
                {
                    "status": "in_progress",
                    "thought_process": "write test",
                    "tool_call": {
                        "name": "write_file",
                        "args": {"filepath": "test_ok.py", "content": PASSING_UNITTEST},
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
            ]),
        )
        self.assertEqual(result, "Task successfully completed and verified by VFS.")
        self.assertTrue(os.path.exists(os.path.join(self.workspace, "test_ok.py")))
        chosen = self._load_jsonl(self.chosen)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["reward"], 1.0)
        self.assertEqual(chosen[0]["task"], "write passing tests")
        self.assertIn("unittest", chosen[0]["verified_command"])
        self.assertEqual(self._load_jsonl(self.rejected), [])


if __name__ == "__main__":
    unittest.main()
