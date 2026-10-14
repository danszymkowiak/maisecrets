"""The Gretel synthetic finance adapter (docs/BENCHMARK.md): one sample per generated document; pii_spans become gold
spans, every unlabelled character is negative. Spans with broken offsets are dropped and counted, not fatal: the
dataset has a few hundred. Made-up records in Gretel's shape.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import unittest

from maisecrets_bench.adapters.datasets import gretel
from maisecrets_bench.domain.labels import LabelTable
from maisecrets_bench.domain.bench_error import BenchError

TEXT = "Contact jo@example.com or call +49 30 1234567 about the account."
TABLE = LabelTable("gretel", {"email": "EMAIL", "phone_number": "PHONE", "company": "OUT_OF_SCOPE"})


def _rec(i, spans, text=TEXT, language="German", split="train", quality=90, document_type="Email"):
    return {"index": i, "level_0": i, "language": language, "generated_text": text,
            "pii_spans": json.dumps(spans), "_split": split, "quality_score": quality,
            "document_type": document_type}


class GretelTests(unittest.TestCase):
    def test_spans_become_gold_with_the_type_of_the_table(self):
        e, p = TEXT.index("jo@"), TEXT.index("+49")
        stats = gretel.Stats()
        (s,) = list(gretel.samples([_rec(7, [{"start": e, "end": e + 14, "label": "email"},
                                             {"start": p, "end": p + 14, "label": "phone_number"}])], TABLE, stats))
        self.assertEqual((s.dataset, s.sample_id, s.group_id, s.language), ("gretel", "train:7", "train:7", "de"))
        self.assertEqual([(TEXT[x.start:x.end], x.maisecrets_type, x.gold) for x in s.spans],
                         [("jo@example.com", "EMAIL", "pos"), ("+49 30 1234567", "PHONE", "pos")])

    def test_the_language_names_become_codes(self):
        for name, code in (("English", "en"), ("France", "fr"), ("Swedish", "sv"), ("Dutch", "nl")):
            (s,) = list(gretel.samples([_rec(1, [], language=name)], TABLE, gretel.Stats()))
            self.assertEqual(s.language, code)

    def test_an_unknown_language_stops_with_its_name(self):
        with self.assertRaisesRegex(BenchError, "'Klingon'"):
            list(gretel.samples([_rec(1, [], language="Klingon")], TABLE, gretel.Stats()))

    def test_a_span_with_broken_offsets_is_dropped_and_counted(self):
        stats = gretel.Stats()
        (s,) = list(gretel.samples([_rec(1, [{"start": 5, "end": 500, "label": "email"},
                                             {"start": 9, "end": 9, "label": "email"},
                                             {"start": 0, "end": 7, "label": "company"}])], TABLE, stats))
        self.assertEqual(len(s.spans), 1)
        self.assertEqual(stats.dropped, 2)

    def test_an_unknown_label_stops_with_its_name(self):
        with self.assertRaisesRegex(BenchError, "'shoe_size'"):
            list(gretel.samples([_rec(1, [{"start": 0, "end": 7, "label": "shoe_size"}])], TABLE, gretel.Stats()))

    def test_a_record_below_quality_90_is_dropped_and_counted(self):
        stats = gretel.Stats()
        out = list(gretel.samples([_rec(1, [], quality=89), _rec(2, [], quality=90), _rec(3, [], quality=95)],
                                  TABLE, stats))
        self.assertEqual([s.sample_id for s in out], ["train:2", "train:3"])
        self.assertEqual(stats.low_quality, 1)

    def test_structured_formats_are_tagged_apart(self):
        for doc, fmt in (("MT940", "structured"), ("CSV", "structured"), ("SWIFT Message", "structured"),
                         ("FIX Protocol", "structured"), ("Email", "unstructured"), ("Tax Return", "unstructured")):
            (s,) = list(gretel.samples([_rec(1, [], document_type=doc)], TABLE, gretel.Stats()))
            self.assertEqual(s.tags, [f"format:{fmt}"], doc)
        self.assertEqual(gretel.STRUCTURED, {"CSV", "EDI", "SWIFT Message", "FIX Protocol", "BAI Format", "XBRL",
                                             "FpML", "MT940"})

    def test_train_and_test_records_with_the_same_index_stay_apart(self):
        out = list(gretel.samples([_rec(1, []), _rec(1, [], split="test")], TABLE, gretel.Stats()))
        self.assertEqual(sorted(s.sample_id for s in out), ["test:1", "train:1"])


if __name__ == "__main__":
    unittest.main()
