"""Floors first, then false positives (TASK-21.8): recall per scoring type with its one-sided Wilson bound and floor
status, false positives per 1,000 tokens per dataset and weighted, and the verdict of a change. Made-up samples.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.domain import floors
from maisecrets_bench.domain import floorscore
from maisecrets_bench.domain.samples import Sample, Span
from maisecrets_bench.domain.score import Detection

FLOORS = """
default_tier = "default"
[tiers.critical]
floor = 0.999
types = ["IBAN"]
[tiers.high]
floor = 0.99
types = ["EMAIL"]
[tiers.default]
floor = "no_regression"
types = ["SECRET_GENERIC"]
[tiers.none]
floor = "none"
types = []
[weights]
gretel = 2.0
"""


def _floors() -> floors.Floors:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "f.toml"
        p.write_text(FLOORS, encoding="utf-8")
        return compose.load_floors(p)


F = _floors()


def _s(ds, sid, text, spans):
    return Sample(ds, sid, sid, "en", text, spans, "dev")


def _pos(t, a, b, label="x"):
    return Span(a, b, label, t, "pos")


def _det(t, a, b):
    return Detection(a, b, t, "r")


class WilsonTests(unittest.TestCase):
    def test_the_rule_of_three(self):
        self.assertGreaterEqual(floorscore.wilson_lower(3000, 3000), 0.999)
        self.assertLess(floorscore.wilson_lower(2000, 2000), 0.999)
        self.assertEqual(floorscore.wilson_lower(0, 0), 0.0)

    def test_status(self):
        self.assertEqual(floorscore.status(3000, 3000, 0.999), "clears")
        self.assertEqual(floorscore.status(2000, 2000, 0.999), "too_few")
        self.assertEqual(floorscore.status(90, 100, 0.99), "gap")
        self.assertEqual(floorscore.status(5, 10, "no_regression"), "no_regression")
        self.assertEqual(floorscore.status(5, 10, "none"), "none")


class SummaryTests(unittest.TestCase):
    def test_recall_per_scoring_type_tokens_and_fp_per_1k(self):
        text = "mail a@b.io and c@d.io " + "word " * 96          # 100 whitespace tokens
        s = _s("gretel", "1", text, [_pos("EMAIL", 5, 11), _pos("EMAIL", 16, 22)])
        det = {("gretel", "1"): [_det("EMAIL", 5, 11), _det("PHONE", 30, 34)]}
        out = floorscore.summarise([s], det, F, {})
        e = out["types"]["EMAIL"]
        self.assertEqual((e["found"], e["n"], e["tier"], e["status"]), (1, 2, "high", "gap"))
        self.assertEqual(out["fp"]["gretel"], {"fp": 1, "tokens": 100, "per_1k": 10.0, "weight": 2.0,
                                               "role": "scored"})
        self.assertEqual(out["objective"], 10.0)

    def test_secret_is_scored_by_its_split_type(self):
        s = _s("gretel", "1", "pass hunter2x", [_pos("SECRET", 5, 13, label="password")])
        out = floorscore.summarise([s], {}, F, {})
        self.assertIn("SECRET_GENERIC", out["types"])
        self.assertNotIn("SECRET", out["types"])

    def test_the_objective_is_weighted_and_leaves_guards_out(self):
        a = _s("gretel", "1", "x " * 1000, [])
        b = _s("creddata", "1", "x " * 1000, [])
        g = _s("synthetic", "1", "x " * 1000, [])
        det = {("gretel", "1"): [_det("PHONE", 0, 1)], ("creddata", "1"): [_det("PHONE", 0, 1)] * 4,
               ("synthetic", "1"): [_det("PHONE", 0, 1)] * 9}
        out = floorscore.summarise([a, b, g], det, F, {"synthetic": "guard"})
        self.assertAlmostEqual(out["objective"], (2 * 1.0 + 1 * 4.0) / 3)

    def test_a_critical_miss_is_listed_without_its_value(self):
        s = _s("gretel", "7", "iban CH93 0076 2011 6238 5295 7", [_pos("IBAN", 5, 31)])
        out = floorscore.summarise([s], {}, F, {})
        self.assertEqual(out["critical_misses"], [{"dataset": "gretel", "sample": "7", "type": "IBAN",
                                                   "start": 5, "end": 31}])

    def test_guards_are_not_pooled_into_the_floors(self):
        s = _s("synthetic", "1", "mail a@b.io", [_pos("EMAIL", 5, 11)])
        out = floorscore.summarise([s], {}, F, {"synthetic": "guard"})
        self.assertNotIn("EMAIL", out["types"])
        self.assertEqual(out["guards"]["synthetic"]["found"], 0)


def _summary(found_by_type: dict, fp_per_1k: float = 1.0, guard=None) -> dict:
    types = {}
    for t, (found, n) in found_by_type.items():
        tier, floor = F.tier_of(t)
        types[t] = {"found": found, "n": n, "tier": tier, "floor": floor, "status": floorscore.status(found, n, floor),
                    "by_dataset": {"gretel": {"found": found, "n": n}}}
    return {"types": types, "objective": fp_per_1k, "fp": {}, "guards": guard or {}, "critical_misses": []}


class VerdictTests(unittest.TestCase):
    def test_fewer_false_positives_with_every_floor_held_is_accepted(self):
        v = floorscore.verdict(_summary({"IBAN": (4000, 4000)}, 2.0), _summary({"IBAN": (4000, 4000)}, 1.5))
        self.assertEqual(v["verdict"], "accepted")
        self.assertAlmostEqual(v["objective_delta"], -0.5)

    def test_a_broken_floor_rejects_and_names_type_and_dataset(self):
        v = floorscore.verdict(_summary({"IBAN": (4000, 4000)}, 2.0), _summary({"IBAN": (3990, 4000)}, 0.1))
        self.assertEqual(v["verdict"], "rejected")
        self.assertIn("IBAN", v["decided_by"][0])
        self.assertIn("gretel", v["decided_by"][0])

    def test_a_find_lost_above_the_floor_is_allowed(self):
        v = floorscore.verdict(_summary({"IBAN": (9000, 9000)}, 2.0), _summary({"IBAN": (8999, 9000)}, 1.0))
        self.assertEqual(v["verdict"], "accepted")

    def test_a_worse_gap_rejects_and_a_narrower_gap_accepts(self):
        base = _summary({"EMAIL": (90, 100)}, 1.0)
        self.assertEqual(floorscore.verdict(base, _summary({"EMAIL": (89, 100)}, 0.5))["verdict"], "rejected")
        v = floorscore.verdict(base, _summary({"EMAIL": (95, 100)}, 1.2))
        self.assertEqual(v["verdict"], "accepted")
        self.assertEqual(v["gaps_narrowed"], ["EMAIL"])

    def test_too_few_and_no_regression_types_must_not_lose_a_find(self):
        for t, n in (("IBAN", 100), ("SECRET_GENERIC", 100)):
            v = floorscore.verdict(_summary({t: (n, n)}, 2.0), _summary({t: (n - 1, n)}, 1.0))
            self.assertEqual(v["verdict"], "rejected", t)

    def test_no_effect_or_more_false_positives_alone_is_neutral(self):
        base = _summary({"IBAN": (4000, 4000)}, 1.0)
        self.assertEqual(floorscore.verdict(base, _summary({"IBAN": (4000, 4000)}, 1.0))["verdict"], "neutral")
        self.assertEqual(floorscore.verdict(base, _summary({"IBAN": (4000, 4000)}, 1.3))["verdict"], "neutral")

    def test_a_worse_guard_rejects(self):
        g0 = {"synthetic": {"found": 10, "fp": 0}}
        g1 = {"synthetic": {"found": 10, "fp": 1}}
        v = floorscore.verdict(_summary({}, 2.0, g0), _summary({}, 1.0, g1))
        self.assertEqual(v["verdict"], "rejected")
        self.assertIn("synthetic", v["decided_by"][0])

    def test_the_worse_of_dev_and_check(self):
        self.assertEqual(floorscore.worse("accepted", "neutral"), "neutral")
        self.assertEqual(floorscore.worse("neutral", "rejected"), "rejected")


if __name__ == "__main__":
    unittest.main()
