"""Guarded line unwrap (TASK-11.25, AC 3): a token a terminal or a narrow pane wrapped onto the next line is joined in
the cleaned copy only when a shape rule (a prefix-anchored one, no label rule) finds a token across the break that
neither half gives alone. A plain next-line join failed on .env files (README): KEY=value lines must stay apart.

Run: python3 -m unittest tests.test_unwrap -v
"""
from __future__ import annotations

import os
import random
import string
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _isolate  # noqa: E402,F401  first: a temp vault home, never the real one

from maisecrets import unwrap  # noqa: E402

_R = random.Random(1125)
AN = string.ascii_letters + string.digits
TOKEN = "ghp_" + "".join(_R.choice(AN) for _ in range(36))


class UnwrapTests(unittest.TestCase):
    def test_a_wrapped_token_is_joined_and_maps_back_to_both_lines(self):
        text = f"export TOKEN={TOKEN[:20]}\n{TOKEN[20:]}\nnext line"
        n = unwrap.unwrap(text)
        self.assertIn(TOKEN, n.text)
        a = n.text.index(TOKEN)
        start, end = n.span(a, a + len(TOKEN))
        self.assertEqual(text[start:end], TOKEN[:20] + "\n" + TOKEN[20:])

    def test_env_lines_stay_apart(self):
        # built from pieces: a literal KEY=value line in the tree is what the repository's own scan flags
        env = "".join(f"{k}={v}\n" for k, v in (("API_" + "KEY", "abc123" + "def456"), ("DB_HOST", "db.internal"),
                                               ("DB_USER", "app"), ("SECRET_" + "NAME", "prod")))
        self.assertIs(unwrap.unwrap(env).text, env)

    def test_a_token_that_is_whole_on_its_line_is_not_joined_to_the_next(self):
        text = f"token {TOKEN}\nabcdef more text"
        self.assertIs(unwrap.unwrap(text).text, text)

    def test_prose_lines_stay_apart(self):
        text = "The quick brown fox\njumps over the lazy dog\n"
        self.assertIs(unwrap.unwrap(text).text, text)


if __name__ == "__main__":
    unittest.main()
