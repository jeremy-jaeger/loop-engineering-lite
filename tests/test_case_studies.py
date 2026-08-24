"""Published case-study logs must stay in the tree."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "docs" / "case-studies" / "logs"

CASES = [
    "01-unverified-complete",
    "02-message-count-is-not-success",
    "03-failed-tests-blocked",
    "04-print-is-not-verification",
    "05-path-jail",
    "06-inference-error",
    "07-search-and-replace-miss",
    "08-escaped-newlines",
    "09-zero-tests-collected",
    "10-command-timeout",
    "11-abort-exports-rejected",
    "12-tests-live-in-implementation",
]


class CaseStudyLogTests(unittest.TestCase):
    def test_all_logs_present_and_nonempty(self):
        for name in CASES:
            path = LOG_DIR / f"{name}.log"
            self.assertTrue(path.is_file(), msg=f"missing {path}")
            self.assertGreater(path.stat().st_size, 20, msg=f"empty {path}")
