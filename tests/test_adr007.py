import json
import os
import tempfile
import unittest

from search import best_of_n
from vfs import VirtualFileSystem
from world_model import SymbolicWorldModel
from loop import run_agent_loop
import memory


PASSING = """import unittest

class SmokeTest(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(True)
"""

FAILING = """import unittest

class SmokeTest(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(False)
"""


class ForkIsolationTest(unittest.TestCase):
    def test_child_write_does_not_mutate_parent_or_host(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        vfs = VirtualFileSystem(base_dir=td.name)
        vfs.write_file("keep.py", "parent = 1\n")
        child = vfs.fork()
        child.write_file("keep.py", "child = 2\n")
        child.write_file("only_child.py", "x = 1\n")
        self.assertEqual(vfs.read_file("keep.py"), "parent = 1\n")
        self.assertIn("Error", vfs.read_file("only_child.py"))
        self.assertFalse(os.path.exists(os.path.join(td.name, "only_child.py")))
        self.assertFalse(os.path.exists(os.path.join(td.name, "keep.py")))

    def test_adopt_copies_fork_without_host_write(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        vfs = VirtualFileSystem(base_dir=td.name)
        child = vfs.fork()
        child.write_file("new.py", "ok\n")
        vfs.adopt(child)
        self.assertEqual(vfs.read_file("new.py"), "ok\n")
        self.assertFalse(os.path.exists(os.path.join(td.name, "new.py")))


class WorldModelRolloutTest(unittest.TestCase):
    def test_rollout_scores_passing_unittest(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        wm = SymbolicWorldModel(base_dir=td.name)
        result = wm.rollout(
            [{"name": "write_file", "args": {"filepath": "test_ok.py", "content": PASSING}}],
            verify_command="python3 -m unittest test_ok.py",
        )
        self.assertEqual(result["value"], 1.0)
        self.assertIsNone(wm.value())
        self.assertIn("Error", wm.vfs.read_file("test_ok.py"))


class BestOfNTest(unittest.TestCase):
    def test_picks_passing_write_and_exports_dpo(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        vfs = VirtualFileSystem(base_dir=td.name)
        dpo = os.path.join(td.name, "search_dpo.jsonl")
        fail = {
            "status": "in_progress",
            "thought_process": "bad tests",
            "tool_call": {
                "name": "write_file",
                "args": {"filepath": "test_ok.py", "content": FAILING},
            },
        }
        win = {
            "status": "in_progress",
            "thought_process": "good tests",
            "tool_call": {
                "name": "write_file",
                "args": {"filepath": "test_ok.py", "content": PASSING},
            },
        }
        chosen, obs, report = best_of_n(
            vfs,
            [fail, win],
            verify_command="python3 -m unittest test_ok.py",
            task="write passing tests",
            dpo_path=dpo,
        )
        self.assertEqual(report["best_value"], 1.0)
        self.assertIn("assertTrue(True)", chosen["tool_call"]["args"]["content"])
        self.assertIn("[SEARCH]", obs)
        self.assertTrue(os.path.exists(dpo))
        with open(dpo) as f:
            pair = json.loads(f.readline())
        self.assertEqual(pair["reward_chosen"], 1.0)
        self.assertEqual(pair["reward_rejected"], 0.0)
        self.assertIn("assertTrue(True)", vfs.read_file("test_ok.py"))
        self.assertFalse(os.path.exists(os.path.join(td.name, "test_ok.py")))

    def test_loop_search_width_selects_passing_candidate(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        orig_ds = memory.DATASET_FILE
        orig_rj = memory.REJECTED_FILE
        orig_dpo = memory.SEARCH_DPO_FILE
        memory.DATASET_FILE = os.path.join(td.name, "chosen.jsonl")
        memory.REJECTED_FILE = os.path.join(td.name, "rejected.jsonl")
        memory.SEARCH_DPO_FILE = os.path.join(td.name, "search_dpo.jsonl")
        self.addCleanup(lambda: setattr(memory, "DATASET_FILE", orig_ds))
        self.addCleanup(lambda: setattr(memory, "REJECTED_FILE", orig_rj))
        self.addCleanup(lambda: setattr(memory, "SEARCH_DPO_FILE", orig_dpo))

        queue = [
            {
                "status": "in_progress",
                "thought_process": "failing tests",
                "tool_call": {
                    "name": "write_file",
                    "args": {"filepath": "test_ok.py", "content": FAILING},
                },
            },
            {
                "status": "in_progress",
                "thought_process": "passing tests",
                "tool_call": {
                    "name": "write_file",
                    "args": {"filepath": "test_ok.py", "content": PASSING},
                },
            },
            {
                "status": "complete",
                "thought_process": "verified",
                "final_answer": "done",
            },
        ]

        def scripted(_messages):
            return queue.pop(0)

        result = run_agent_loop(
            "write passing tests",
            max_iterations=4,
            workspace=td.name,
            enable_reflection=False,
            call_model=scripted,
            search_width=2,
            verify_command="python3 -m unittest test_ok.py",
        )
        self.assertEqual(result, "done")
        self.assertTrue(os.path.exists(os.path.join(td.name, "test_ok.py")))
        with open(os.path.join(td.name, "test_ok.py")) as f:
            self.assertIn("assertTrue(True)", f.read())


if __name__ == "__main__":
    unittest.main()
