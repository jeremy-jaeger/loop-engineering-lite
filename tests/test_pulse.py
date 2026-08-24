"""Pulse generator — no network required."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_pulse", ROOT / "scripts" / "generate_pulse.py")
pulse = importlib.util.module_from_spec(SPEC)
sys.modules["generate_pulse"] = pulse
SPEC.loader.exec_module(pulse)


class HistoryTests(unittest.TestCase):
    def test_one_point_per_day_overwrites(self):
        h = pulse.append_history([], {"stars": 1, "forks": 0, "watchers": 0, "open_issues": 0, "contributors": ["a"]}, "2026-08-24")
        h = pulse.append_history(h, {"stars": 2, "forks": 0, "watchers": 0, "open_issues": 0, "contributors": ["a"]}, "2026-08-24")
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["stars"], 2)

    def test_next_day_appends(self):
        h = pulse.append_history([], {"stars": 1, "forks": 0, "watchers": 0, "open_issues": 0, "contributors": []}, "2026-08-24")
        h = pulse.append_history(h, {"stars": 4, "forks": 1, "watchers": 0, "open_issues": 0, "contributors": []}, "2026-08-25")
        self.assertEqual(len(h), 2)
        self.assertEqual(pulse.star_delta(h), 3)

    def test_sparkline_has_points(self):
        hist = [{"date": "d", "stars": n} for n in (0, 2, 5)]
        pts = pulse.sparkline_path(hist, 0, 0, 100, 10)
        self.assertEqual(len(pts.split()), 3)


class ReadmePatchTests(unittest.TestCase):
    def test_markers_replaced(self):
        body = "before\n<!-- pulse:start -->\nold\n<!-- pulse:end -->\nafter\n"
        out = pulse.patch_readme(body, "<!-- pulse:start -->\nnew\n<!-- pulse:end -->")
        self.assertIn("new", out)
        self.assertNotIn("old", out)
        self.assertTrue(out.startswith("before"))

    def test_narrate_mentions_delta(self):
        stats = {"stars": 5, "forks": 1, "watchers": 0, "open_issues": 2, "contributors": ["ada"]}
        hist = [
            {"date": "a", "stars": 3},
            {"date": "b", "stars": 5},
        ]
        text = pulse.narrate(stats, hist, "now")
        self.assertIn("+2", text)
        self.assertIn("`ada`", text)
        html = pulse.html_blurb(stats, hist, "now")
        self.assertIn("<code>ada</code>", html)
        self.assertNotIn("**", html)


class LoadHistoryTests(unittest.TestCase):
    def test_missing_file(self):
        self.assertEqual(pulse.load_history(Path("/tmp/no-such-pulse-history.json")), [])

    def test_roundtrip(self):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "h.json"
        path.write_text("[]", encoding="utf-8")
        self.assertEqual(pulse.load_history(path), [])
        td.cleanup()


if __name__ == "__main__":
    unittest.main()
