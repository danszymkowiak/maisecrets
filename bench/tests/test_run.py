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
    return [Sample("toy", "a", "g1", "en", TEXT, [Span(m, m + len(MAIL), "EMAIL", "EMAIL", "pos")], "dev",
                   ["format:unstructured"]),
            Sample("toy", "b", "g2", "de", FREE, [], "check", ["format:structured"]),
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

    def test_scores_per_tag(self):
        tags = self.summary["datasets"]["toy"]["tags"]
        self.assertEqual(sorted(tags), ["format:structured", "format:unstructured"])
        self.assertEqual((tags["format:unstructured"]["tp"], tags["format:unstructured"]["samples"]), (1, 1))
        self.assertEqual(tags["format:structured"]["tp"], 0)
        self.assertGreaterEqual(tags["format:structured"]["fp"], 1)
        report = (self.out / "report.md").read_text(encoding="utf-8")
        self.assertIn("| format:structured |", report)

    def test_each_language_ran_with_its_own_regions(self):
        groups = self.summary["groups"]
        self.assertIn("de", groups["de"]["regions"])
        self.assertIn("us", groups["en"]["regions"])
        self.assertNotIn("de", groups["en"]["regions"])

    def test_rules_that_never_fired_are_listed(self):
        self.assertGreater(len(self.summary["never_fired"]), 100)
        self.assertNotIn("email", self.summary["never_fired"])

    def test_the_report_and_the_metrics_hold_no_value(self):
        for name in ("report.md", "metrics.json", "detections.parquet"):
            text = (self.out / name).read_bytes().decode("utf-8", errors="replace")
            for value in (MAIL, "zq.tester", PHONE, "9876 5432"):
                self.assertNotIn(value, text, name)

    def test_the_detections_are_saved_and_reload_the_same(self):
        det = run.load_detections(self.out / "detections.parquet")
        self.assertIn(("toy", "a"), det)
        self.assertEqual(run.score_all(_samples(), det)["toy"]["dev"].found, 1)

    def test_a_mutation_that_loses_a_find_is_rejected_and_reruns_only_where_the_rule_fired(self):
        from maisecrets_bench import mutate
        from maisecrets_bench.mutation import Mutation
        samples, det, names = mutate.baseline(self.out, self.out.parent)
        m = Mutation("no email", "", [{"op": "disable", "rule": "email"}])
        (r,) = mutate.evaluate([m], samples, det, {}, jobs=2)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["rerun_samples"], 1, "only sample a had an e-mail hit")
        self.assertIn("toy: recall", " ".join(r["reasons"]))
        self.assertEqual(r["verdict"], "rejected")
        text = mutate.report([r], self.out)
        self.assertIn("| rejected |", text)
        self.assertIn("Rejected: toy:", text)
        self.assertIn("at most 0.50 points", text)

    def test_the_report_names_the_overall_score(self):
        self.assertIn("Overall score", (self.out / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
