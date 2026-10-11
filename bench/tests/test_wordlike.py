"""Word-likeness (TASK-11.22): the share of a value covered by dictionary words, and a character-bigram score.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import wordlike

WORDS = frozenset({"user", "name", "max", "retry", "count", "connection", "timeout", "pool", "size", "the"})


class SegmentTests(unittest.TestCase):
    def test_identifiers_split_on_case_and_separators(self):
        self.assertEqual(wordlike.chunks("maxRetryCount"), ["max", "retry", "count"])
        self.assertEqual(wordlike.chunks("CONNECTION_POOL-size2"), ["connection", "pool", "size"])

    def test_coverage_counts_letters_inside_words(self):
        self.assertAlmostEqual(wordlike.coverage("maxRetryCount", WORDS), 1.0)
        self.assertAlmostEqual(wordlike.coverage("connectiontimeout", WORDS), 1.0, msg="glued words segment")
        self.assertLess(wordlike.coverage("Xq7vR2mK9pLw", WORDS), 0.3)
        self.assertEqual(wordlike.coverage("12345678", WORDS), 0.0)

    def test_short_words_do_not_count(self):
        self.assertEqual(wordlike.coverage("at", frozenset({"at"})), 0.0)


class BigramTests(unittest.TestCase):
    def test_english_scores_above_random_letters(self):
        table = wordlike.bigram_table(["connection", "timeout", "username", "password", "retry", "counter",
                                       "station", "nation", "mention", "ration"])
        self.assertGreater(wordlike.bigram_score("connection", table), wordlike.bigram_score("xqzvkjwq", table))


if __name__ == "__main__":
    unittest.main()
