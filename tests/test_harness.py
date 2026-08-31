"""Harness unit tests — no inference, no network."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loop import truncate_text  # noqa: E402
from vfs import VirtualFileSystem  # noqa: E402
from tools import execute_tool  # noqa: E402
import memory  # noqa: E402


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

    def test_commit_writes_host(self):
        self.vfs.write_file("out/a.txt", "committed")
        self.vfs.write_file(
            "test_ok.py",
            "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
        )
        score, _ = self.vfs.simulate_command("python3 -m unittest test_ok.py")
        self.assertEqual(score, 1.0)
        self.assertTrue(self.vfs.commit_to_reality())
        path = os.path.join(self.td.name, "out", "a.txt")
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "committed")


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

    def test_export_jsonl(self):
        memory.export_trajectory_jsonl([{"role": "user", "content": "hi"}])
        self.assertTrue(os.path.exists("dataset.jsonl"))
        with open("dataset.jsonl", encoding="utf-8") as f:
            line = f.read().strip()
        self.assertIn("hi", line)


if __name__ == "__main__":
    unittest.main()
