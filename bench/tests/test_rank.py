"""The leave-one-out ranking (TASK-18.2, decided with the user 2026-10-12): pure wins first (false positives saved, no
find lost), then trades by weighted false positives saved per weighted find lost (small counts flagged), then the
protected rules (a floor broken, a gap worse or a guard lost: never candidates).

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import rank


def result(name, fp, found=None, decided=()):
    """fp: dataset -> (before, after); found: type -> (tier, before, after)"""
    return {"name": name, "verdict": "rejected" if decided else "accepted", "decided_by": list(decided),
            "datasets": {d: {"fp": list(v), "tp": [0, 0]} for d, v in fp.items()},
            "floors": {t: {"base": {"found": b, "tier": tier}, "mutated": {"found": a, "tier": tier}}
                       for t, (tier, b, a) in (found or {}).items()}}


WEIGHTS = {"gretel": 2.0}
LOST = "SECRET_GENERIC: a find lost"


class RankTests(unittest.TestCase):
    def test_a_removal_that_saves_false_positives_and_loses_nothing_is_a_pure_win(self):
        (row,) = rank.rows([result("Disable x", {"gretel": (10, 4), "creddata": (5, 4)})], WEIGHTS)
        self.assertEqual((row.group, row.fp_saved, row.weighted_fp_saved, row.tp_lost), ("pure", 7, 13.0, 0))

    def test_a_removal_that_loses_finds_is_a_trade_weighted_by_tier(self):
        (row,) = rank.rows([result("Disable y", {"creddata": (100, 40)},
                                   {"SECRET_GENERIC": ("default", 50, 48), "PHONE": ("high", 10, 10)},
                                   ["SECRET_GENERIC: a find lost, 50/90 -> 48/90"])], WEIGHTS)
        self.assertEqual((row.group, row.tp_lost, row.weighted_tp_lost), ("trade", 2, 2.0))
        self.assertEqual(row.ratio, 30.0)
        self.assertTrue(row.weak, "two finds lost is weak evidence")

    def test_a_broken_floor_a_worse_gap_or_a_lost_guard_protects_the_rule(self):
        for reason in ("IBAN: floor 0.999 broken, 10/10 -> 9/10", "CARD: gap worse, 8/10 -> 7/10",
                       "guard synthetic: finds 5 -> 4, false positives 0 -> 0"):
            with self.subTest(reason=reason):
                (row,) = rank.rows([result("Disable z", {"gretel": (9, 1)}, {"CARD": ("critical", 8, 7)}, [reason])],
                                   WEIGHTS)
                self.assertEqual(row.group, "protected")

    def test_the_order_is_pure_wins_then_trades_by_ratio_then_protected(self):
        rows = rank.rows([
            result("p-small", {"gretel": (3, 2)}),
            result("p-big", {"creddata": (30, 2)}),
            result("t-low", {"creddata": (12, 2)}, {"SECRET_GENERIC": ("default", 9, 4)}, [LOST]),
            result("t-high", {"creddata": (100, 0)}, {"SECRET_GENERIC": ("default", 9, 8)}, [LOST]),
            result("prot", {"gretel": (99, 0)}, {"IBAN": ("critical", 5, 4)}, ["IBAN: gap worse, 5/9 -> 4/9"]),
            result("none", {"gretel": (3, 3)}),
        ], WEIGHTS)
        self.assertEqual([r.name for r in rank.ordered(rows)], ["p-big", "p-small", "t-high", "t-low", "prot", "none"])

    def test_the_report_names_each_group_and_flags_weak_evidence(self):
        text = rank.report(rank.rows([result("Disable a", {"gretel": (3, 1)}),
                                      result("Disable b", {"creddata": (9, 1)}, {"SECRET_GENERIC": ("default", 3, 2)},
                                             ["SECRET_GENERIC: a find lost"])], WEIGHTS), "base1")
        for part in ("## Pure wins", "## Trades", "## Protected", "Disable a", "Disable b", "weak", "base1"):
            self.assertIn(part, text)


if __name__ == "__main__":
    unittest.main()
