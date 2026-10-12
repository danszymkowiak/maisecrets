"""The ai4privacy adapter (docs/BENCHMARK.md): local and opt-in, for the user's own non-commercial measurement. One
sample per record; privacy_mask spans are the gold, a span whose offsets miss its value is dropped and counted.
Made-up records in the dataset's shape.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench.adapters import ai4privacy
from maisecrets_bench.labels import LabelTable
from maisecrets_bench.paths import BenchError

TEXT = "Mail zq@example.org or call 030 1234567, Mr Testerson."
TABLE = LabelTable("ai4privacy", {"EMAIL": "EMAIL", "TEL": "PHONE", "LASTNAME1": "OUT_OF_SCOPE"})


def _rec(rid, mask, text=TEXT, language="German", split="train"):
    return {"id": rid, "source_text": text, "privacy_mask": mask, "language": language, "set": split}


def _m(label, value, text=TEXT):
    i = text.index(value)
    return {"label": label, "start": i, "end": i + len(value), "value": value}


class Ai4PrivacyTests(unittest.TestCase):
    def test_spans_become_gold(self):
        st = ai4privacy.Stats()
        (s,) = list(ai4privacy.samples([_rec("r1", [_m("EMAIL", "zq@example.org"), _m("TEL", "030 1234567"),
                                                    _m("LASTNAME1", "Testerson")])], TABLE, st))
        self.assertEqual((s.dataset, s.sample_id, s.language), ("ai4privacy", "train:r1", "de"))
        self.assertEqual([(TEXT[x.start:x.end], x.maisecrets_type, x.gold) for x in s.spans],
                         [("zq@example.org", "EMAIL", "pos"), ("030 1234567", "PHONE", "pos"),
                          ("Testerson", "OUT_OF_SCOPE", "pos")])

    def test_the_leading_token_of_a_continuation_record_is_uncertain(self):
        # TASK-33: ai4privacy cut long texts into records ...A, ...B, ...; a continuation starts mid-value and its
        # first token is left unlabelled. A detection there counts neither as found nor as a false alarm.
        text = "N, WA14 5RW and more text"
        (s,) = list(ai4privacy.samples([_rec("40768C", [], text=text)], TABLE, ai4privacy.Stats()))
        self.assertEqual([(x.start, x.end, x.gold, x.maisecrets_type) for x in s.spans],
                         [(0, 2, "uncertain", "OUT_OF_SCOPE")])
        from maisecrets_bench import score
        d = score.Detection(0, 1, "EMAIL", "email")
        self.assertEqual(score.classify(s, d, True), "neutral")
        self.assertEqual(score.classify(s, score.Detection(8, 11, "EMAIL", "email"), True), "fp")

    def test_a_first_record_or_a_labelled_start_gets_no_uncertain_span(self):
        for rid, mask in (("40768A", []), ("r1", []), ("40768B", [_m("EMAIL", "zq@example.org", "zq@example.org x")])):
            text = "zq@example.org x" if mask else TEXT
            with self.subTest(rid=rid):
                (s,) = list(ai4privacy.samples([_rec(rid, mask, text=text)], TABLE, ai4privacy.Stats()))
                self.assertNotIn("uncertain", [x.gold for x in s.spans])

    def test_a_span_whose_offsets_miss_its_value_is_dropped_and_counted(self):
        st = ai4privacy.Stats()
        bad = dict(_m("EMAIL", "zq@example.org"), start=0)
        (s,) = list(ai4privacy.samples([_rec("r1", [bad])], TABLE, st))
        self.assertEqual((s.spans, st.dropped), ([], 1))

    def test_an_unknown_label_or_language_stops_with_its_name(self):
        with self.assertRaisesRegex(BenchError, "'SHOE'"):
            list(ai4privacy.samples([_rec("r1", [_m("SHOE", "Testerson")])], TABLE, ai4privacy.Stats()))
        with self.assertRaisesRegex(BenchError, "'Klingon'"):
            list(ai4privacy.samples([_rec("r1", [], language="Klingon")], TABLE, ai4privacy.Stats()))

    def test_the_error_never_shows_a_value(self):
        try:
            list(ai4privacy.samples([_rec("r1", [_m("SHOE", "Testerson")])], TABLE, ai4privacy.Stats()))
        except BenchError as exc:
            self.assertNotIn("Testerson", str(exc))


if __name__ == "__main__":
    unittest.main()
