"""The runner end to end on a tiny made-up dataset with the real detector: the counts land in metrics.json and the
report, and neither holds a value.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import run, schema
from maisecrets_bench.schema import Sample, Span

MAIL = "zq.tester@example-mail.org"        # made up; the report must not show it
PHONE = "+49 30 9876 5432"
TEXT = f"Write to {MAIL} today. Nothing else here."
FREE = f"Call {PHONE} please."


def _samples():
    m = TEXT.index(MAIL)
    return [Sample("toy", "a", "g1", "en", TEXT, [Span(m, m + len(MAIL), "EMAIL", "EMAIL", "pos")], "dev"),
            Sample("toy", "b", "g2", "de", FREE, [], "check"),
            Sample("toy", "c", "g3", "en", "no secrets in this line", [Span(0, 2, "X", "EMAIL", "pos")], "dev")]


class RunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        schema.write(_samples(), d / "toy.parquet")
        (d / "manifest.json").write_text(json.dumps({"datasets": {"toy": {"version": "t1"}}}))
        cls.summary = run.run(d, ["toy"], d / "out", jobs=2)
        cls.out = d / "out"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_counts(self):
        a = self.summary["datasets"]["toy"]["all"]
        self.assertEqual((a["tp"], a["found"], a["fn"]), (1, 1, 1), "the e-mail found, the fake span missed")
        self.assertGreaterEqual(a["fp"], 1, "the phone number in unlabelled text is a false positive")
        self.assertIn("dev", self.summary["datasets"]["toy"])
        self.assertIn("check", self.summary["datasets"]["toy"])

    def test_each_language_ran_with_its_own_regions(self):
        groups = self.summary["groups"]
        self.assertIn("de", groups["de"]["regions"])
        self.assertIn("us", groups["en"]["regions"])
        self.assertNotIn("de", groups["en"]["regions"])

    def test_rules_that_never_fired_are_listed(self):
        self.assertGreater(len(self.summary["never_fired"]), 100)
        self.assertNotIn("email", self.summary["never_fired"])

    def test_the_report_and_the_metrics_hold_no_value(self):
        for name in ("report.md", "metrics.json"):
            text = (self.out / name).read_text(encoding="utf-8")
            for value in (MAIL, "zq.tester", PHONE, "9876 5432"):
                self.assertNotIn(value, text, name)

    def test_the_report_names_the_overall_score(self):
        self.assertIn("Overall score", (self.out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
