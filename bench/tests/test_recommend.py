"""The recommendations page (TASK-11.14, the user's choice of 2026-10-11: one combined page per round): the baseline
per dataset, the floor status per type, the accepted rule changes with their per-dataset deltas, the rejected ones
with their reason, and the rules that never fire. A local-only dataset (ai4privacy) never appears on it: the page is
meant for upstream."""
from __future__ import annotations

import unittest

from maisecrets_bench import recommend

BASE = {"datasets": {"gretel": {"all": {"precision": 0.74, "recall": 0.81, "score": 0.77, "tp": 100, "fp": 35}},
                     "ai4privacy": {"all": {"precision": 0.97, "recall": 0.63, "score": 0.76, "tp": 9, "fp": 1}}},
        "floors": {"types": {"IBAN": {"tier": "critical", "floor": 0.999, "found": 99, "n": 100, "lower": 0.95,
                                      "status": "gap", "by_dataset": {"gretel": {"found": 99, "n": 100}}}}},
        "never_fired": ["slack-legacy-token", "etsy-access-token"], "overall": 0.84}
MUT = {"baseline": "/x/runs/20261012-141549", "roles": {}, "results": [
    {"name": "Drop uk-postcode", "why": "false alarms on Gretel", "verdict": "accepted", "objective_delta": -0.01,
     "gaps_narrowed": [], "decided_by": [], "changes": [{"op": "disable", "rule": "uk-postcode"}],
     "datasets": {"gretel": {"role": "scored", "tp": [100, 100], "fp": [35, 20],
                             "base": {"precision": 0.74, "recall": 0.81},
                             "mutated": {"precision": 0.83, "recall": 0.81}},
                  "ai4privacy": {"role": "scored", "tp": [9, 9], "fp": [1, 0],
                                 "base": {"precision": 0.97, "recall": 0.63},
                                 "mutated": {"precision": 1.0, "recall": 0.63}}}},
    {"name": "Drop iban", "why": "test", "verdict": "rejected", "objective_delta": -0.02, "gaps_narrowed": [],
     "decided_by": ["IBAN: gap worse, 99/100 -> 0/100"], "changes": [{"op": "disable", "rule": "iban"}],
     "datasets": {}}]}


class RecommendTests(unittest.TestCase):
    def setUp(self):
        self.page = recommend.page(BASE, [MUT], local_only={"ai4privacy"}, baseline_id="20261012-141549")

    def test_a_local_only_dataset_never_appears(self):
        self.assertNotIn("ai4privacy", self.page)

    def test_the_baseline_floors_and_never_fired_rules(self):
        self.assertIn("20261012-141549", self.page)
        self.assertIn("| gretel | 74.0% | 81.0% |", self.page)
        self.assertIn("IBAN", self.page)
        self.assertIn("slack-legacy-token", self.page)

    def test_accepted_changes_with_deltas_and_rejected_ones_with_their_reason(self):
        accepted = self.page.split("## Rejected")[0]
        self.assertIn("Drop uk-postcode", accepted)
        self.assertIn("35 -> 20", accepted)
        self.assertIn("IBAN: gap worse", self.page.split("## Rejected")[1])

    def test_it_says_how_to_reproduce(self):
        self.assertIn("bench/setup.py", self.page)
        self.assertIn("bench/mutate.py", self.page)


if __name__ == "__main__":
    unittest.main()
