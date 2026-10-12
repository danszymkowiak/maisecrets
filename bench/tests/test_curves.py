"""Precision-recall curves for rules with a score (docs/BENCHMARK.md, Metrics): an entropy threshold (a carried
gitleaks rule) is swept over the candidates of a relaxed run; a Presidio context gate gives two points. Pure functions.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import curves


class CurveTests(unittest.TestCase):
    def test_sweeping_a_threshold(self):
        # (score, is_tp): higher entropy, truer
        pts = [(1.0, False), (2.0, False), (3.0, True), (3.5, False), (4.0, True), (4.5, True)]
        c = curves.sweep(pts)
        self.assertEqual(c[0], {"threshold": 1.0, "tp": 3, "fp": 3, "precision": 0.5, "retained": 1.0})
        last = c[-1]
        self.assertEqual((last["threshold"], last["tp"], last["fp"]), (4.5, 1, 0))
        self.assertAlmostEqual(last["retained"], 1 / 3)

    def test_area_under_the_curve(self):
        perfect = curves.sweep([(1.0, True), (2.0, True)])
        self.assertAlmostEqual(curves.auc(perfect), 1.0)
        mixed = curves.sweep([(1.0, False), (2.0, True), (3.0, False), (4.0, True)])
        self.assertLess(curves.auc(mixed), 1.0)
        self.assertGreater(curves.auc(mixed), 0.0)

    def test_no_true_positive_gives_no_curve(self):
        self.assertIsNone(curves.auc(curves.sweep([(1.0, False), (2.0, False)])))

    def test_the_point_at_the_current_threshold(self):
        c = curves.sweep([(1.0, False), (3.0, True), (4.0, True)])
        self.assertEqual(curves.at(c, 3.5)["tp"], 1)
        self.assertEqual(curves.at(c, 0.0)["tp"], 2)

    def test_the_most_precise_threshold_that_keeps_a_share_of_the_true_positives(self):
        c = curves.sweep([(1.0, True), (2.0, False), (3.0, True), (4.0, False), (5.0, True)])
        self.assertEqual(curves.best(c, 2 / 3)["threshold"], 3.0)
        self.assertEqual(curves.best(c, 1.0)["threshold"], 1.0)
        self.assertIsNone(curves.best([], 0.5))

    def test_the_two_points_of_a_context_gate(self):
        p = curves.gate_points([(True, True), (True, False), (False, False), (False, True)])
        self.assertEqual(p["with_context"], {"tp": 1, "fp": 1, "precision": 0.5})
        self.assertEqual(p["without_gate"], {"tp": 2, "fp": 2, "precision": 0.5})


if __name__ == "__main__":
    unittest.main()
