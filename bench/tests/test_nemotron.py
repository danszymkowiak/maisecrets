"""The Nemotron-PII adapter (TASK-11.34): one sample per record, its spans (a Python literal in the data) become gold,
the split is fixed by uid, and locale and document format become tags the report scores apart. Made-up records in
Nemotron's shape.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import unittest

from maisecrets_bench.adapters import nemotron
from maisecrets_bench.labels import LabelTable, load
from maisecrets_bench.paths import BenchError
from maisecrets_bench.split import split_of

TEXT = "Brian pays with 5490 3479 1287 6543 and writes to bq@example.com."
TABLE = LabelTable("nemotron", {"first_name": "OUT_OF_SCOPE", "credit_debit_card": "CARD", "email": "EMAIL"})


def _rec(uid="u1", spans=None, text=TEXT, locale="us", fmt="unstructured"):
    if spans is None:
        c, e = text.index("5490"), text.index("bq@")
        spans = [{"start": 0, "end": 5, "text": "Brian", "label": "first_name"},
                 {"start": c, "end": c + 19, "text": "5490 3479 1287 6543", "label": "credit_debit_card"},
                 {"start": e, "end": e + 14, "text": "bq@example.com", "label": "email"}]
    return {"uid": uid, "locale": locale, "document_format": fmt, "text": text, "spans": repr(spans),
            "_split": "test"}


class NemotronTests(unittest.TestCase):
    def test_spans_become_gold_with_the_type_of_the_table(self):
        (s,) = list(nemotron.samples([_rec()], TABLE, nemotron.Stats()))
        self.assertEqual((s.dataset, s.sample_id, s.group_id, s.language), ("nemotron", "us:u1", "u1", "en"))
        self.assertEqual([(TEXT[x.start:x.end], x.maisecrets_type, x.gold) for x in s.spans],
                         [("Brian", "OUT_OF_SCOPE", "pos"), ("5490 3479 1287 6543", "CARD", "pos"),
                          ("bq@example.com", "EMAIL", "pos")])

    def test_the_split_is_fixed_by_uid(self):
        for uid in ("a", "b", "c", "d"):
            (s,) = list(nemotron.samples([_rec(uid)], TABLE, nemotron.Stats()))
            self.assertEqual(s.split, split_of("nemotron", uid))

    def test_the_us_and_intl_records_of_one_uid_stay_apart_in_one_split(self):
        # every uid of the data has a us and an intl record with other text (run 20261012-010002 mixed them up)
        out = list(nemotron.samples([_rec("u7"), _rec("u7", locale="intl")], TABLE, nemotron.Stats()))
        self.assertEqual(sorted(s.sample_id for s in out), ["intl:u7", "us:u7"])
        self.assertEqual({s.group_id for s in out}, {"u7"})
        self.assertEqual(len({s.split for s in out}), 1)

    def test_locale_and_format_become_tags(self):
        (s,) = list(nemotron.samples([_rec(locale="intl", fmt="structured")], TABLE, nemotron.Stats()))
        self.assertEqual(s.tags, ["locale:intl", "format:structured"])

    def test_a_span_whose_text_differs_only_in_case_or_type_is_kept(self):
        # the data holds a few thousand: "black" over "Black", the number 42 for the text "42"
        text = "Age 42, Black."
        spans = [{"start": 4, "end": 6, "text": 42, "label": "email"},
                 {"start": 8, "end": 13, "text": "black", "label": "email"}]
        (s,) = list(nemotron.samples([_rec(text=text, spans=spans)], TABLE, nemotron.Stats()))
        self.assertEqual(len(s.spans), 2)

    def test_a_span_with_broken_offsets_or_other_text_is_dropped_and_counted(self):
        stats = nemotron.Stats()
        spans = [{"start": 5, "end": 500, "text": "x", "label": "email"},
                 {"start": 0, "end": 5, "text": "Peter", "label": "first_name"}]
        (s,) = list(nemotron.samples([_rec(spans=spans)], TABLE, stats))
        self.assertEqual((len(s.spans), stats.dropped), (0, 2))

    def test_an_unknown_label_stops_with_its_name(self):
        with self.assertRaisesRegex(BenchError, "'shoe_size'"):
            list(nemotron.samples([_rec(spans=[{"start": 0, "end": 5, "text": "Brian", "label": "shoe_size"}])],
                                  TABLE, nemotron.Stats()))

    def test_spans_are_read_as_a_literal_never_run(self):
        rec = _rec()
        rec["spans"] = "__import__('os').getcwd()"
        with self.assertRaises(BenchError):
            list(nemotron.samples([rec], TABLE, nemotron.Stats()))

    def test_the_table_maps_every_label_of_the_data(self):
        table = load("nemotron")
        self.assertEqual(set(table.mapping), nemotron.LABELS)
        self.assertEqual(table.type_of("credit_debit_card"), "CARD")
        self.assertEqual(table.type_of("first_name"), "OUT_OF_SCOPE")


if __name__ == "__main__":
    unittest.main()
