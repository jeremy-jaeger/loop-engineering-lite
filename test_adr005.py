import json
import os
import tempfile
import unittest

from improve.dataset import prepare, is_verified_chosen, build_dpo_pairs
from improve.evaluate import run_suite
from improve.promote import promote
from improve.train import train
import improve.config as cfg
import memory


def _trace(task, reward, command, assistant_blob):
    return {
        "task": task,
        "reward": reward,
        "verified_command": command,
        "messages": [
            {"role": "user", "content": task},
            {"role": "assistant", "content": assistant_blob},
        ],
    }


CHOSEN_BLOB = json.dumps({
    "thought_process": "write tests",
    "status": "in_progress",
    "tool_call": {"name": "write_file", "args": {"filepath": "x.py", "content": "ok"}},
})
REJECTED_BLOB = json.dumps({
    "thought_process": "guess",
    "status": "complete",
    "final_answer": "done",
})


class DatasetGateTest(unittest.TestCase):
    def test_unverified_reward_is_not_chosen(self):
        row = _trace("t", 1.0, None, CHOSEN_BLOB)
        self.assertFalse(is_verified_chosen(row))
        self.assertFalse(is_verified_chosen(_trace("t", 0.0, "python3 -m pytest", CHOSEN_BLOB)))

    def test_prepare_rejects_empty_verified_set(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        chosen = os.path.join(td.name, "chosen.jsonl")
        rejected = os.path.join(td.name, "rejected.jsonl")
        with open(chosen, "w") as f:
            f.write(json.dumps(_trace("t", 0.0, None, REJECTED_BLOB)) + "\n")
            f.write(json.dumps(_trace("t", 1.0, None, CHOSEN_BLOB)) + "\n")
        open(rejected, "w").close()
        with self.assertRaises(ValueError):
            prepare(chosen_path=chosen, rejected_path=rejected, out_dir=os.path.join(td.name, "mlx"))

    def test_prepare_filters_and_builds_dpo_pairs(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        chosen = os.path.join(td.name, "chosen.jsonl")
        rejected = os.path.join(td.name, "rejected.jsonl")
        task = "Use TDD to write clamp"
        with open(chosen, "w") as f:
            f.write(json.dumps(_trace(task, 1.0, "python3 -m unittest test_clamp.py", CHOSEN_BLOB)) + "\n")
            f.write(json.dumps(_trace("other", 0.0, None, CHOSEN_BLOB)) + "\n")
        with open(rejected, "w") as f:
            f.write(json.dumps(_trace(task, 0.0, None, REJECTED_BLOB)) + "\n")
        summary = prepare(chosen_path=chosen, rejected_path=rejected, out_dir=os.path.join(td.name, "mlx"))
        self.assertEqual(summary["chosen_verified"], 1)
        self.assertEqual(summary["dpo_pairs"], 1)
        train_path = os.path.join(td.name, "mlx", "train.jsonl")
        with open(train_path) as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reward"], 1.0)
        self.assertIn("tool_call", rows[0]["messages"][1]["content"])

    def test_dpo_requires_same_task(self):
        chosen = [_trace("A", 1.0, "pytest", CHOSEN_BLOB)]
        rejected = [_trace("B", 0.0, None, REJECTED_BLOB)]
        self.assertEqual(build_dpo_pairs(chosen, rejected), [])


class TrainPlanTest(unittest.TestCase):
    def test_plan_only_does_not_claim_trained_weights(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        chosen = os.path.join(td.name, "chosen.jsonl")
        with open(chosen, "w") as f:
            f.write(json.dumps(_trace("task", 1.0, "python3 -m pytest", CHOSEN_BLOB)) + "\n")
        orig_spec = cfg.TRAIN_SPEC_FILE
        orig_ad = cfg.ADAPTERS_DIR
        cfg.ADAPTERS_DIR = td.name
        cfg.TRAIN_SPEC_FILE = os.path.join(td.name, "train_spec.json")
        self.addCleanup(lambda: setattr(cfg, "TRAIN_SPEC_FILE", orig_spec))
        self.addCleanup(lambda: setattr(cfg, "ADAPTERS_DIR", orig_ad))
        spec = train(
            chosen_path=chosen,
            rejected_path=os.path.join(td.name, "missing.jsonl"),
            out_dir=os.path.join(td.name, "mlx"),
            adapter_dir=os.path.join(td.name, "lora"),
            plan_only=True,
        )
        self.assertEqual(spec["status"], "plan_only")
        self.assertEqual(spec["chosen_verified"], 1)
        self.assertTrue(spec["mlx_train"])


class PromoteGateTest(unittest.TestCase):
    def _patch_cfg(self, td):
        orig = {
            "TRAIN_SPEC_FILE": cfg.TRAIN_SPEC_FILE,
            "CURRENT_ADAPTER": cfg.CURRENT_ADAPTER,
            "ADAPTERS_DIR": cfg.ADAPTERS_DIR,
        }
        cfg.ADAPTERS_DIR = td
        cfg.TRAIN_SPEC_FILE = os.path.join(td, "train_spec.json")
        cfg.CURRENT_ADAPTER = os.path.join(td, "current.json")

        def restore():
            for k, v in orig.items():
                setattr(cfg, k, v)
        self.addCleanup(restore)

    def test_blocks_untrained_adapter(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self._patch_cfg(td.name)
        eval_path = os.path.join(td.name, "eval.json")
        baseline_path = os.path.join(td.name, "baseline.json")
        with open(eval_path, "w") as f:
            json.dump({"win_rate": 1.0, "n": 3, "evaluated_at": "now"}, f)
        with open(cfg.TRAIN_SPEC_FILE, "w") as f:
            json.dump({"status": "plan_only"}, f)
        decision = promote(eval_path=eval_path, baseline_path=baseline_path, min_delta=0.05)
        self.assertFalse(decision["promoted"])
        self.assertFalse(os.path.exists(cfg.CURRENT_ADAPTER))

    def test_promotes_when_fused_and_win_rate_beats_baseline(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self._patch_cfg(td.name)
        eval_path = os.path.join(td.name, "eval.json")
        baseline_path = os.path.join(td.name, "baseline.json")
        with open(eval_path, "w") as f:
            json.dump({"win_rate": 0.67, "n": 3, "evaluated_at": "now"}, f)
        with open(baseline_path, "w") as f:
            json.dump({"win_rate": 0.0, "n": 3}, f)
        with open(cfg.TRAIN_SPEC_FILE, "w") as f:
            json.dump({
                "status": "fused",
                "ollama_model": "loop-lite-improved",
                "fused_dir": "adapters/fused",
            }, f)
        decision = promote(eval_path=eval_path, baseline_path=baseline_path, min_delta=0.05)
        self.assertTrue(decision["promoted"])
        self.assertTrue(os.path.exists(cfg.CURRENT_ADAPTER))
        self.assertTrue(os.path.exists(os.path.join(td.name, "Modelfile")))


class EvalSuiteTest(unittest.TestCase):
    def test_scripted_failures_are_zero_win_rate(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        orig_ds = memory.DATASET_FILE
        orig_rj = memory.REJECTED_FILE
        memory.DATASET_FILE = os.path.join(td.name, "chosen.jsonl")
        memory.REJECTED_FILE = os.path.join(td.name, "rejected.jsonl")
        self.addCleanup(lambda: setattr(memory, "DATASET_FILE", orig_ds))
        self.addCleanup(lambda: setattr(memory, "REJECTED_FILE", orig_rj))

        def always_complete(_messages):
            return {"status": "complete", "thought_process": "skip", "final_answer": "nope"}

        orig_eval = cfg.EVAL_FILE
        orig_ad = cfg.ADAPTERS_DIR
        cfg.ADAPTERS_DIR = td.name
        cfg.EVAL_FILE = os.path.join(td.name, "last_eval.json")
        self.addCleanup(lambda: setattr(cfg, "EVAL_FILE", orig_eval))
        self.addCleanup(lambda: setattr(cfg, "ADAPTERS_DIR", orig_ad))

        report = run_suite(
            call_model=always_complete,
            tasks=[{"id": "x", "prompt": "do x"}],
            max_iterations=1,
        )
        self.assertEqual(report["win_rate"], 0.0)
        self.assertEqual(report["wins"], 0)


if __name__ == "__main__":
    unittest.main()
