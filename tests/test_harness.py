"""Harness unit tests — no inference, no network."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import memory  # noqa: E402
from loop import truncate_text  # noqa: E402
from tools import execute_tool  # noqa: E402
from vfs import VirtualFileSystem, is_verification_command  # noqa: E402


class TruncateTests(unittest.TestCase):
    def test_short_passthrough(self):
        self.assertEqual(truncate_text("hello"), "hello")

    def test_long_keeps_head_and_tail(self):
        blob = "A" * 2000 + "MID" + "Z" * 2000
        out = truncate_text(blob, max_chars=100)
        self.assertIn("TRUNCATED BY HARNESS", out)
        self.assertTrue(out.startswith("A"))
        self.assertTrue(out.endswith("Z"))
        self.assertLess(len(out), len(blob))


class VerificationCommandTests(unittest.TestCase):
    def test_pytest_and_unittest_count(self):
        self.assertTrue(is_verification_command("python3 -m pytest -q"))
        self.assertTrue(is_verification_command("python3 -m pytest test_stack.py -q"))
        self.assertTrue(is_verification_command("python3 -m unittest test_ok.py"))
        self.assertTrue(is_verification_command("python3 test_ok.py"))
        self.assertFalse(is_verification_command("python3 main.py"))
        self.assertFalse(is_verification_command("python3 hello.py"))
        self.assertFalse(is_verification_command("ls -la"))
        self.assertFalse(is_verification_command(""))


class VfsTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.vfs = VirtualFileSystem(base_dir=self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_write_and_read_stay_in_memory(self):
        self.vfs.write_file("hello.txt", "world")
        self.assertEqual(self.vfs.read_file("hello.txt"), "world")
        self.assertFalse(os.path.exists(os.path.join(self.td.name, "hello.txt")))

    def test_simulate_success_and_failure(self):
        self.vfs.write_file("ok.py", "print('ok')\n")
        score, out = self.vfs.simulate_command("python3 ok.py")
        self.assertEqual(score, 1.0)
        self.assertIn("ok", out)

        score, _ = self.vfs.simulate_command("python3 missing.py")
        self.assertEqual(score, 0.0)

    def test_generic_success_is_not_verification(self):
        self.vfs.write_file("ok.py", "print('ok')\n")
        self.vfs.simulate_command("python3 ok.py")
        self.assertFalse(self.vfs.is_task_verified())
        self.assertFalse(self.vfs.commit_to_reality())
        self.assertFalse(os.path.exists(os.path.join(self.td.name, "ok.py")))

    def test_commit_blocked_without_verification(self):
        self.vfs.write_file("out/a.txt", "committed")
        self.assertFalse(self.vfs.commit_to_reality())
        self.assertFalse(os.path.exists(os.path.join(self.td.name, "out", "a.txt")))

    def test_commit_writes_only_touched_paths(self):
        host_untouched = os.path.join(self.td.name, "untouched.txt")
        with open(host_untouched, "w", encoding="utf-8") as f:
            f.write("host-original")
        vfs = VirtualFileSystem(base_dir=self.td.name)
        vfs.write_file("agent.py", "print(1)\n")
        vfs.write_file(
            "test_ok.py",
            "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
        )
        score, _ = vfs.simulate_command("python3 -m unittest test_ok.py")
        self.assertEqual(score, 1.0)
        self.assertTrue(vfs.commit_to_reality())
        self.assertTrue(os.path.exists(os.path.join(self.td.name, "agent.py")))
        with open(host_untouched, encoding="utf-8") as f:
            self.assertEqual(f.read(), "host-original")

    def test_path_jail_rejects_parent_and_absolute(self):
        self.assertIn("Error", self.vfs.write_file("../escape.py", "nope"))
        self.assertNotIn("../escape.py", self.vfs.state)
        abs_path = os.path.join(os.path.dirname(self.td.name), "outside.py")
        self.assertIn("Error", self.vfs.write_file(abs_path, "nope"))

    def test_fork_is_isolated(self):
        self.vfs.write_file("a.py", "one")
        child = self.vfs.fork()
        child.write_file("a.py", "two")
        child.write_file("b.py", "child-only")
        self.assertEqual(self.vfs.read_file("a.py"), "one")
        self.assertTrue(self.vfs.read_file("b.py").startswith("Error:"))
        self.vfs.adopt(child)
        self.assertEqual(self.vfs.read_file("a.py"), "two")
        self.assertEqual(self.vfs.read_file("b.py"), "child-only")

    def test_timeout_scores_zero(self):
        score, out = self.vfs.simulate_command("python3 -c 'import time; time.sleep(5)'", timeout=1)
        self.assertEqual(score, 0.0)
        self.assertIn("timed out", out.lower())


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.vfs = VirtualFileSystem(base_dir=self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_write_list_read_replace(self):
        execute_tool(self.vfs, "write_file", {"filepath": "a.py", "content": "x = 1\n"})
        listing = execute_tool(self.vfs, "list_files", {})
        self.assertIn("a.py", listing)
        body = execute_tool(self.vfs, "read_file", {"filepath": "a.py"})
        self.assertIn("1 |", body)
        execute_tool(
            self.vfs,
            "search_and_replace",
            {"filepath": "a.py", "old_code": "x = 1", "new_code": "x = 2"},
        )
        self.assertIn("x = 2", self.vfs.read_file("a.py"))

    def test_run_command_labels_success(self):
        execute_tool(self.vfs, "write_file", {"filepath": "t.py", "content": "print(1)\n"})
        obs = execute_tool(self.vfs, "run_command", {"command": "python3 t.py"})
        self.assertIn("SIMULATION VERIFIED SUCCESS", obs)

    def test_unknown_tool(self):
        self.assertIn("does not exist", execute_tool(self.vfs, "explode", {}))

    def test_replace_miss_tells_model_to_rewrite(self):
        execute_tool(self.vfs, "write_file", {"filepath": "a.py", "content": "x = 1\n"})
        obs = execute_tool(
            self.vfs,
            "search_and_replace",
            {"filepath": "a.py", "old_code": "does not exist", "new_code": "x = 2"},
        )
        self.assertIn("old_code` block not found", obs)
        self.assertIn("write_file", obs)

    def test_normalizes_escaped_newlines(self):
        execute_tool(
            self.vfs,
            "write_file",
            {"filepath": "a.py", "content": "def f():\\n    return 1\\n"},
        )
        body = self.vfs.read_file("a.py")
        self.assertIn("\n", body)
        self.assertNotIn("\\n", body)

    def test_strips_trailing_brace_junk(self):
        execute_tool(
            self.vfs,
            "write_file",
            {"filepath": "a.py", "content": "x = 'ok'}}}"},
        )
        self.assertEqual(self.vfs.read_file("a.py"), "x = 'ok'")

    def test_tool_args_as_json_string(self):
        obs = execute_tool(
            self.vfs, "write_file", '{"filepath": "b.py", "content": "z = 3\\n"}'
        )
        self.assertIn("VFS Updated", obs)
        self.assertIn("z = 3", self.vfs.read_file("b.py"))


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.td.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.td.cleanup()

    def test_save_and_load_knowledge(self):
        memory.save_knowledge("task", "Always write tests first.")
        loaded = memory.load_knowledge()
        self.assertIn("Always write tests first.", loaded)
        self.assertIn("CRITICAL PAST LEARNINGS", loaded)

    def test_export_jsonl_default_reward(self):
        memory.export_trajectory_jsonl([{"role": "user", "content": "hi"}])
        self.assertTrue(os.path.exists("dataset.jsonl"))
        with open("dataset.jsonl", encoding="utf-8") as f:
            line = f.read().strip()
        self.assertIn("hi", line)
        self.assertIn('"reward": 1.0', line)

    def test_rejected_export_goes_to_data(self):
        memory.export_trajectory_jsonl(
            [{"role": "user", "content": "fail"}], reward=0.0, task="x"
        )
        path = os.path.join("data", "rejected.jsonl")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as f:
            row = f.read()
        self.assertIn('"reward": 0.0', row)


if __name__ == "__main__":
    unittest.main()
