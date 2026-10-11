"""Is a dataset worth keeping (docs/BENCHMARK.md)? Rescoring saved detections without a rule (a probe) and the table
of scope, saturation, discrimination and overlap per dataset.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import usefulness
from maisecrets_bench.schema import Sample, Span
from maisecrets_bench.score import Detection

OOS = "OUT_OF_SCOPE"


def _data():
    a = [Sample("a", f"a{i}", f"g{i}", "en", "x" * 50, [Span(0, 10, "pw", "SECRET", "pos")], "dev") for i in range(4)]
    b = [Sample("b", f"b{i}", f"h{i}", "en", "x" * 50, [Span(0, 10, "n", OOS, "pos")], "dev") for i in range(4)]
    det = {("a", f"a{i}"): [Detection(0, 10, "SECRET", "r1")] for i in range(4)}
    det[("a", "a0")].append(Detection(20, 30, "SECRET", "r2"))
    det.update({("b", f"b{i}"): [] for i in range(4)})
    det[("b", "b0")] = [Detection(30, 40, "PHONE", "r2")]
    return a + b, det


class RescoreTests(unittest.TestCase):
    def test_dropping_a_rule_drops_its_detections(self):
        samples, det = _data()
        base = usefulness.rescore(samples, det, frozenset())
        without = usefulness.rescore(samples, det, frozenset({"r1"}))
        self.assertEqual((base["a"].found, without["a"].found), (4, 0))


class TableTests(unittest.TestCase):
    def setUp(self):
        samples, det = _data()
        self.t = usefulness.table(samples, det, probes=["r1", "r2"])

    def test_scope(self):
        self.assertEqual((self.t["a"]["in_scope_pos"], self.t["a"]["pos"]), (4, 4))
        self.assertEqual((self.t["b"]["in_scope_pos"], self.t["b"]["in_scope_share"]), (0, 0.0))

    def test_rules_firing_and_only_there(self):
        self.assertEqual(self.t["a"]["rules_firing"], 2)
        self.assertEqual(self.t["a"]["rules_only_here"], ["r1"])
        self.assertEqual(self.t["b"]["rules_only_here"], [])

    def test_probe_sensitivity(self):
        self.assertLess(self.t["a"]["probes"]["r1"], 0, "without r1 dataset a loses all its finds")
        self.assertGreater(self.t["b"]["probes"]["r2"], 0, "without r2 dataset b has no false alarm left")
        self.assertEqual(self.t["b"]["probes"]["r1"], 0)
        self.assertEqual(self.t["a"]["probes_moved"], 2)
        self.assertEqual(self.t["b"]["probes_moved"], 1)


class OverlapTests(unittest.TestCase):
    def test_datasets_that_always_move_together_are_flagged(self):
        deltas = {"a": {"p1": -0.1, "p2": 0.0, "p3": 0.2}, "b": {"p1": -0.2, "p2": 0.0, "p3": 0.4},
                  "c": {"p1": 0.1, "p2": -0.3, "p3": 0.0}}
        same = usefulness.same_direction(deltas)
        self.assertEqual(same[("a", "b")], 1.0)
        self.assertLess(same[("a", "c")], 1.0)


if __name__ == "__main__":
    unittest.main()
