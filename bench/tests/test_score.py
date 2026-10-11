"""Scoring (docs/BENCHMARK.md, What counts and Metrics): detections against gold spans, as counts. A pure function
of spans and detections; the detector is not involved.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench import score
from maisecrets_bench.schema import Sample, Span
from maisecrets_bench.score import Detection

OOS = "OUT_OF_SCOPE"


def _s(spans, text="x" * 100, dataset="toy", split="dev"):
    return Sample(dataset, "s", "g", "en", text, spans, split)


def _d(start, end, type_="SECRET", rule="r1"):
    return Detection(start, end, type_, rule)


class OutcomeTests(unittest.TestCase):
    def test_a_detection_on_an_in_scope_positive_is_a_true_positive_and_finds_it(self):
        c = score.score_sample(_s([Span(10, 20, "pw", "SECRET", "pos")]), [_d(12, 18)], unlabelled_negative=True)
        self.assertEqual((c.tp, c.fp, c.fn, c.found), (1, 0, 0, 1))

    def test_a_missed_positive_is_a_false_negative(self):
        c = score.score_sample(_s([Span(10, 20, "pw", "SECRET", "pos")]), [], unlabelled_negative=True)
        self.assertEqual((c.tp, c.fp, c.fn), (0, 0, 1))

    def test_a_type_mismatch_still_counts_and_is_listed(self):
        c = score.score_sample(_s([Span(10, 20, "mail", "EMAIL", "pos")]), [_d(10, 20, "SECRET")],
                               unlabelled_negative=True)
        self.assertEqual((c.tp, c.fn), (1, 0))
        self.assertEqual(c.confusion, {("EMAIL", "SECRET"): 1})

    def test_a_detection_on_an_out_of_scope_positive_is_neutral_and_counted_as_coverage(self):
        c = score.score_sample(_s([Span(10, 20, "name", OOS, "pos")]), [_d(10, 20)], unlabelled_negative=True)
        self.assertEqual((c.tp, c.fp, c.fn, c.oos_found, c.oos_total), (0, 0, 0, 1, 1))

    def test_a_detection_on_unlabelled_text_is_a_false_positive_where_unlabelled_text_is_negative(self):
        c = score.score_sample(_s([]), [_d(50, 60)], unlabelled_negative=True)
        self.assertEqual((c.fp, c.unreviewed), (1, 0))

    def test_on_creddata_unlabelled_text_is_unreviewed_and_a_negative_span_is_a_false_positive(self):
        c = score.score_sample(_s([Span(30, 40, "Password", "SECRET", "neg")]), [_d(50, 60), _d(32, 35)],
                               unlabelled_negative=False)
        self.assertEqual((c.fp, c.unreviewed), (1, 1))

    def test_a_type_the_dataset_does_not_judge_counts_nowhere(self):
        # CredData labels credentials only: an e-mail address on a line it marked "not a credential" is no false
        # alarm of maisecrets, which hides e-mail addresses on purpose (found by the probes, 2026-10-11)
        spans = [Span(30, 60, "Password", "SECRET", "neg")]
        c = score.score_sample(_s(spans), [_d(35, 50, "EMAIL"), _d(70, 80, "EMAIL"), _d(32, 40, "SECRET")],
                               unlabelled_negative=False, judged=frozenset({"SECRET"}))
        self.assertEqual((c.fp, c.unreviewed, c.unjudged), (1, 0, 2))

    def test_a_judged_type_mismatch_on_a_positive_is_still_a_true_positive(self):
        c = score.score_sample(_s([Span(10, 20, "pw", "SECRET", "pos")]), [_d(10, 20, "EMAIL")],
                               unlabelled_negative=False, judged=frozenset({"SECRET"}))
        self.assertEqual((c.tp, c.unjudged), (1, 0))

    def test_a_detection_on_an_uncertain_span_counts_nowhere(self):
        c = score.score_sample(_s([Span(30, 40, "Token", "SECRET", "uncertain")]), [_d(30, 40)],
                               unlabelled_negative=True)
        self.assertEqual((c.tp, c.fp, c.fn, c.unreviewed), (0, 0, 0, 0))

    def test_a_positive_wins_over_a_negative_span_under_the_same_detection(self):
        spans = [Span(10, 30, "Password", "SECRET", "neg"), Span(15, 25, "Password", "SECRET", "pos")]
        c = score.score_sample(_s(spans), [_d(10, 30)], unlabelled_negative=False)
        self.assertEqual((c.tp, c.fp), (1, 0))

    def test_two_detections_on_one_positive_are_two_true_positives_and_one_find(self):
        c = score.score_sample(_s([Span(10, 30, "pw", "SECRET", "pos")]), [_d(10, 15), _d(20, 30)],
                               unlabelled_negative=True)
        self.assertEqual((c.tp, c.found, c.fn), (2, 1, 0))

    def test_per_rule_counts(self):
        c = score.score_sample(_s([Span(10, 20, "pw", "SECRET", "pos")]), [_d(10, 20, rule="a"), _d(50, 60, rule="b")],
                               unlabelled_negative=True)
        self.assertEqual(c.rules, {"a": {"hits": 1, "tp": 1, "fp": 0}, "b": {"hits": 1, "tp": 0, "fp": 1}})

    def test_per_type_counts(self):
        spans = [Span(10, 20, "pw", "SECRET", "pos"), Span(40, 45, "mail", "EMAIL", "pos")]
        c = score.score_sample(_s(spans), [_d(10, 20), _d(70, 80, "PHONE")], unlabelled_negative=True)
        self.assertEqual(c.by_type["SECRET"], {"tp": 1, "fp": 0, "found": 1, "fn": 0})
        self.assertEqual(c.by_type["EMAIL"], {"tp": 0, "fp": 0, "found": 0, "fn": 1})
        self.assertEqual(c.by_type["PHONE"], {"tp": 0, "fp": 1, "found": 0, "fn": 0})


class ClassifyAgreesTests(unittest.TestCase):
    def test_classify_gives_the_same_counts_as_score_sample(self):
        import random
        rnd = random.Random(7)
        golds, types = ("pos", "neg", "uncertain"), ("SECRET", "EMAIL", OOS)
        for _ in range(500):
            spans = []
            for _ in range(rnd.randint(0, 4)):
                a = rnd.randint(0, 90)
                spans.append(Span(a, a + rnd.randint(1, 10), "l", rnd.choice(types), rnd.choice(golds)))
            dets = []
            for _ in range(rnd.randint(0, 4)):
                a = rnd.randint(0, 90)
                dets.append(_d(a, a + rnd.randint(1, 10), rnd.choice(("SECRET", "EMAIL", "PHONE"))))
            neg, judged = rnd.random() < 0.5, rnd.choice((None, frozenset({"SECRET"})))
            c = score.score_sample(_s(spans), dets, neg, judged)
            kinds = [score.classify(_s(spans), d, neg, judged) for d in dets]
            self.assertEqual((c.tp, c.fp, c.unreviewed, c.unjudged),
                             (kinds.count("tp"), kinds.count("fp"), kinds.count("unreviewed"), kinds.count("unjudged")))


class MetricTests(unittest.TestCase):
    def test_precision_recall_f1(self):
        m = score.metrics(score.Counts(tp=8, fp=2, found=6, fn=4))
        self.assertAlmostEqual(m["precision"], 0.8)
        self.assertAlmostEqual(m["recall"], 0.6)
        self.assertAlmostEqual(m["f1"], 2 * 0.8 * 0.6 / 1.4)

    def test_no_positives_means_no_recall_and_the_score_is_the_clean_sample_rate(self):
        # precision without a possible true positive is 0 at the first false alarm: TAB scored 0% with 4 false
        # alarms in 1,268 documents (first baseline, 2026-10-11). The share of samples left alone measures it
        m = score.metrics(score.Counts(tp=0, fp=4, samples=1268, clean=1264))
        self.assertIsNone(m["recall"])
        self.assertAlmostEqual(m["clean_rate"], 1264 / 1268)
        self.assertEqual(m["score"], m["clean_rate"])

    def test_a_sample_is_clean_without_a_false_positive(self):
        a = score.score_sample(_s([]), [_d(1, 5)], unlabelled_negative=True)
        b = score.score_sample(_s([]), [], unlabelled_negative=True)
        self.assertEqual(((a.samples, a.clean), (b.samples, b.clean)), ((1, 0), (1, 1)))

    def test_no_detection_at_all_is_full_precision(self):
        self.assertEqual(score.metrics(score.Counts())["precision"], 1.0)

    def test_counts_add(self):
        a = score.Counts(tp=1, fp=1, rules={"r": {"hits": 2, "tp": 1, "fp": 1}}, confusion={("A", "B"): 1})
        b = score.Counts(tp=2, fn=1, rules={"r": {"hits": 1, "tp": 1, "fp": 0}}, confusion={("A", "B"): 2})
        c = a + b
        self.assertEqual((c.tp, c.fp, c.fn), (3, 1, 1))
        self.assertEqual(c.rules["r"], {"hits": 3, "tp": 2, "fp": 1})
        self.assertEqual(c.confusion, {("A", "B"): 3})

    def test_the_overall_score_weights_every_dataset_equally(self):
        self.assertAlmostEqual(score.overall({"a": 0.9, "b": 0.5, "c": 0.1}), 0.5)


if __name__ == "__main__":
    unittest.main()
