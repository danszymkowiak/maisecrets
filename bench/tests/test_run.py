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


class PoolTests(unittest.TestCase):
    def test_workers_start_without_a_unix_socket(self):
        # Python 3.14's default on Linux, forkserver, opens a Unix socket, which the Claude Code sandbox denies;
        # spawn talks over pipes and is the default on macOS and Windows already
        self.assertEqual(run.POOL_CONTEXT.get_start_method(), "spawn")


class OlderDetectorTests(unittest.TestCase):
    """The bench measures an older maisecrets too (MAISECRETS_BENCH_DETECTOR, user 2026-10-14: the fork against the
    version it started from). A plain run uses only scan(text) and rules(), which every version has."""

    def test_a_plain_run_calls_scan_without_a_ruleset(self):
        import types
        calls = []

        def scan(text):     # the old signature: no ruleset keyword
            calls.append(text)
            return [types.SimpleNamespace(start=0, end=2, type="EMAIL", kind="email")]
        old = types.SimpleNamespace(scan=scan, rules=lambda: [types.SimpleNamespace(id="email")],
                                    active_regions=lambda: types.SimpleNamespace(regions=("generic",),
                                                                                 languages=("en",)))
        saved = run._detect, run._RULESET
        try:
            run._detect, run._RULESET = old, None
            self.assertEqual([d.type for d in run._detections("ab")], ["EMAIL"])
            self.assertEqual(run._describe()["rules"], ["email"])
        finally:
            run._detect, run._RULESET = saved
        self.assertEqual(calls, ["ab"])

    def test_a_type_the_older_detector_lacks_is_no_error(self):
        from unittest import mock
        from maisecrets_bench import detector
        self.assertTrue(detector.unknown_type("NO_SUCH_TYPE"))
        with mock.patch.object(detector, "OLDER", True):
            self.assertFalse(detector.unknown_type("NO_SUCH_TYPE"))


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

    def test_a_cc_by_dataset_is_attributed_and_a_local_one_is_flagged(self):
        notes = "\n".join(run.licence_notes(["nemotron", "mendeley", "ai4privacy", "gretel"]))
        self.assertIn("Nemotron-PII", notes)
        self.assertIn("10.17632/tzrjx692jy", notes)
        self.assertIn("non-commercial", notes)
        self.assertEqual(run.licence_notes(["gretel"]), [])

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
        self.assertEqual(r["verdict"], "rejected")
        self.assertIn("EMAIL: gap worse", r["decided_by"][0])
        self.assertIn("toy", r["decided_by"][0])
        self.assertEqual(r["old_verdict"], "rejected", "the earlier verdict stays as a comparison")
        self.assertIn("toy: recall", " ".join(r["reasons"]))
        text = mutate.report([r], self.out)
        self.assertIn("| rejected |", text)
        self.assertIn("Decided by: EMAIL: gap worse", text)
        self.assertIn("| EMAIL | high | 0.99 |", text)
        self.assertIn("Misses of a critical type after the change", text)

    def test_the_baseline_report_shows_floor_status_and_false_positives_per_1k_tokens(self):
        m = json.loads((self.out / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(m["floors"]["types"]["EMAIL"]["status"], "gap")
        self.assertGreater(m["floors"]["fp"]["toy"]["per_1k"], 0)
        report = (self.out / "report.md").read_text(encoding="utf-8")
        self.assertIn("## Recall floors", report)
        self.assertIn("| EMAIL | high | 0.99 | 1 / 2 |", report)
        self.assertIn("false positives per 1,000 tokens", report)
        self.assertTrue((self.out / "critical_misses.tsv").exists())

    def test_the_report_names_the_overall_score(self):
        self.assertIn("Overall score", (self.out / "report.md").read_text(encoding="utf-8"))


class LocaleGroupTests(unittest.TestCase):
    """TASK-28: a sample tagged with a locale whose country has rules of its own (locale:de_CH) runs in a group with
    that region; every other sample keeps its language's group."""

    AHV = "756.9217.0769.85"        # the ZAS example

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        swiss = f"AHV-Nr. {cls.AHV} des Arbeitnehmers"
        a = swiss.index(cls.AHV)
        samples = [Sample("toy", "ch", "g1", "de", swiss, [Span(a, a + len(cls.AHV), "AHV", "CH_AHV", "pos")], "dev",
                          ["locale:de_CH"]),
                   Sample("toy", "de", "g2", "de", swiss, [Span(a, a + len(cls.AHV), "AHV", "CH_AHV", "pos")], "dev"),
                   Sample("toy", "fr", "g3", "fr", "rien", [], "dev", ["locale:fr_FR"])]
        schema.write(samples, d / "toy.parquet")
        (d / "manifest.json").write_text(json.dumps({"datasets": {"toy": {"version": "t1"}}}))
        cls.summary = run.run(d, ["toy"], d / "out", jobs=1)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_swiss_locale_runs_with_region_ch_and_the_others_keep_their_group(self):
        groups = self.summary["groups"]
        self.assertIn("ch", groups["de:de_CH"]["regions"])
        self.assertNotIn("ch", groups["de"]["regions"])
        self.assertIn("fr", groups, "a locale without rules of its own stays in its language's group")
        self.assertNotIn("fr:fr_FR", groups)

    def test_the_ahv_number_is_found_only_in_the_swiss_document(self):
        t = self.summary["datasets"]["toy"]["all"]["by_type"]["CH_AHV"]
        self.assertEqual((t["tp"], t["fn"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
