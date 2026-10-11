"""The dev/check split (docs/BENCHMARK.md, Dev and check: no folds): by group, deterministic, about 70/30.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import split


class SplitTests(unittest.TestCase):
    def test_the_same_group_always_lands_on_the_same_side(self):
        self.assertEqual(split.split_of("creddata", "repo-7"), split.split_of("creddata", "repo-7"))

    def test_a_group_is_never_on_both_sides(self):
        groups = [f"g{i % 50}" for i in range(1000)]
        sides: dict[str, set] = {}
        for g in groups:
            sides.setdefault(g, set()).add(split.split_of("toy", g))
        self.assertTrue(all(len(s) == 1 for s in sides.values()))

    def test_about_seventy_percent_go_to_dev(self):
        n = sum(split.split_of("toy", f"g{i}") == "dev" for i in range(10_000))
        self.assertTrue(6700 <= n <= 7300, n)

    def test_the_value_is_pinned_so_every_machine_agrees(self):
        # a change of the salt or the hash moves every sample: this pin turns red first
        self.assertEqual([split.split_of("toy", f"g{i}") for i in range(8)], PINNED)

    def test_the_dataset_is_part_of_the_key(self):
        a = [split.split_of("one", f"g{i}") for i in range(200)]
        b = [split.split_of("two", f"g{i}") for i in range(200)]
        self.assertNotEqual(a, b)


PINNED = ["dev", "dev", "dev", "check", "dev", "dev", "dev", "dev"]   # frozen 2026-10-11

if __name__ == "__main__":
    unittest.main()
