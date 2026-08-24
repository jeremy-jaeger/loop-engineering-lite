"""CLI parsing — no Ollama."""
import tempfile
import unittest
from unittest import mock

from main import build_parser, cli_entry


class CliTests(unittest.TestCase):
    def test_prompt_joins_words(self):
        args = build_parser().parse_args(["Use", "TDD", "to", "write", "x"])
        self.assertEqual(" ".join(args.prompt), "Use TDD to write x")
        self.assertEqual(args.workspace, ".")
        self.assertEqual(args.max_iterations, 10)
        self.assertFalse(args.no_reflect)

    def test_flags(self):
        args = build_parser().parse_args(
            ["--workspace", "/tmp/demo", "--max-iterations", "4", "--no-reflect", "task"]
        )
        self.assertEqual(args.workspace, "/tmp/demo")
        self.assertEqual(args.max_iterations, 4)
        self.assertTrue(args.no_reflect)

    def test_cli_entry_returns_1_on_unverified_abort(self):
        td = tempfile.TemporaryDirectory()
        try:
            with mock.patch("main.run_agent_loop", return_value=None):
                code = cli_entry(["--workspace", td.name, "--no-reflect", "do nothing"])
            self.assertEqual(code, 1)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
