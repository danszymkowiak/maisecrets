"""Leave-one-out (TASK-18): one disable mutation per rule that fired in a run, written as TOML files that
files.load_mutation reads back.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters import files
from maisecrets_bench.domain import loo

METRICS = {"rules": {
    "us-ssn#2": {"hits": 4, "tp": 1, "fp": 3, "by_dataset": {}},
    "email": {"hits": 90, "tp": 88, "fp": 2, "by_dataset": {}},
    "silent": {"hits": 0, "tp": 0, "fp": 0, "by_dataset": {}},
}}


class LeaveOneOutTests(unittest.TestCase):
    def test_one_disable_per_rule_that_fired_most_hits_first(self):
        muts = loo.mutations(METRICS)
        self.assertEqual([sorted(m.disabled) for m in muts], [["email"], ["us-ssn#2"]])
        self.assertTrue(all(m.disable_only for m in muts))
        self.assertIn("90 hits", muts[0].why)

    def test_the_written_files_load_back_as_the_same_mutations(self):
        muts = loo.mutations(METRICS)
        with tempfile.TemporaryDirectory() as d:
            paths = files.write_mutations(muts, Path(d))
            self.assertEqual([p.name for p in paths], ["leave-out-email.toml", "leave-out-us-ssn-2.toml"])
            back = [files.load_mutation(p) for p in paths]
        self.assertEqual([(m.name, m.why, m.changes) for m in back], [(m.name, m.why, m.changes) for m in muts])

    def test_a_run_without_rules_gives_nothing(self):
        self.assertEqual(loo.mutations({"rules": {}}), [])


if __name__ == "__main__":
    unittest.main()
