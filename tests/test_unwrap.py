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

    def test_the_rules_are_asked_only_where_a_long_token_run_meets_the_break(self):
        # TASK-37: asking the rules at every break between word characters cost 517 ms on 120 KB of prose
        asked = []

        def hits(s):
            asked.append(s)
            return []
        prose = "the build step reads configuration\nfrom the environment and writes\na report per module\n"
        unwrap.unwrap(prose * 50, hits)
        self.assertEqual(asked, [])
        unwrap.unwrap(f"export TOKEN={TOKEN[:20]}\n{TOKEN[20:]}\n", hits)
        self.assertTrue(asked)

    def test_a_short_token_wrapped_in_its_middle_is_still_joined(self):
        short = TOKEN[:24]    # ghp_ and 20 characters: the guard's lower bound is 24 across the break
        text = f"t {short[:12]}\n{short[12:]}\n"
        n = unwrap.unwrap(text, lambda s: [(s.index(short), s.index(short) + len(short))] if short in s else [])
        self.assertIn(short, n.text)



class UnwrapStageTests(unittest.TestCase):
    """unwrap as the last normaliser stage (detect.NORMALISE, bench op normalise): after the other stages, so a wrapped
    token in a coloured terminal capture is joined too, and the scan's span covers both lines of the original."""

    def test_the_stage_joins_after_the_other_stages_and_maps_back(self):
        from maisecrets import normalise
        text = f"\x1b[32mexport TOKEN={TOKEN[:20]}\x1b[0m\n\x1b[32m{TOKEN[20:]}\x1b[0m\n"
        n = normalise.normalise(text, ("ansi", "unwrap"))
        a = n.text.index(TOKEN)
        start, end = n.span(a, a + len(TOKEN))
        self.assertEqual(text[start:end], TOKEN[:20] + "\x1b[0m\n\x1b[32m" + TOKEN[20:])

    def test_a_scan_with_the_stage_redacts_both_lines(self):
        import dataclasses
        from maisecrets import detect
        rs = dataclasses.replace(detect.default_ruleset(), normalise=("unwrap",))
        text = f"export TOKEN={TOKEN[:20]}\n{TOKEN[20:]}\n"
        spans = [(m.start, m.end) for m in detect.scan(text, ruleset=rs)]
        self.assertTrue(any(text[a:b] == TOKEN[:20] + "\n" + TOKEN[20:] for a, b in spans), spans)


if __name__ == "__main__":
    unittest.main()
