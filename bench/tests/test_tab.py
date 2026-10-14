"""The TAB adapter (docs/BENCHMARK.md, TAB): one sample per court document; a mention is pos when either annotator
marked it DIRECT or QUASI, neg when every annotator said NO_MASK. A made-up document in TAB's format.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters.datasets import tab
from maisecrets_bench.domain.labels import LabelTable
from maisecrets_bench.domain.bench_error import BenchError

TEXT = "The applicant, Mr Test Person, lodged application no. 12345/01 on 3 May 2001."
TABLE = LabelTable("tab", {t: "OUT_OF_SCOPE" for t in ("PERSON", "CODE", "DATETIME", "ORG")})


def _m(mid, etype, start, end, ident, text=TEXT):
    return {"entity_mention_id": mid, "entity_type": etype, "start_offset": start, "end_offset": end,
            "span_text": text[start:end], "identifier_type": ident, "edit_type": "check", "entity_id": mid,
            "confidential_status": "NOT_CONFIDENTIAL"}


def _doc(doc_id, annotations, text=TEXT):
    return {"doc_id": doc_id, "text": text, "dataset_type": "dev", "task": "x", "meta": {}, "quality_checked": True,
            "annotations": {a: {"entity_mentions": ms} for a, ms in annotations.items()}}


class TabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _write(self, docs, name="echr_dev.json"):
        (self.root / name).write_text(json.dumps(docs), encoding="utf-8")

    def test_one_sample_per_document_with_the_union_of_the_annotators(self):
        p = TEXT.index("Mr Test Person")
        c = TEXT.index("12345/01")
        d = TEXT.index("3 May 2001")
        self._write([_doc("001-1", {
            "ann1": [_m("a", "PERSON", p, p + 14, "DIRECT"), _m("b", "CODE", c, c + 8, "NO_MASK"),
                     _m("c", "DATETIME", d, d + 10, "NO_MASK")],
            "ann2": [_m("a", "PERSON", p, p + 14, "NO_MASK"), _m("b", "CODE", c, c + 8, "QUASI"),
                     _m("c", "DATETIME", d, d + 10, "NO_MASK")]})])
        (s,) = list(tab.samples(self.root, TABLE))
        self.assertEqual((s.dataset, s.group_id, s.language), ("tab", "001-1", "en"))
        got = {(TEXT[sp.start:sp.end], sp.gold, sp.label, sp.maisecrets_type) for sp in s.spans}
        self.assertEqual(got, {("Mr Test Person", "pos", "PERSON", "OUT_OF_SCOPE"),
                               ("12345/01", "pos", "CODE", "OUT_OF_SCOPE"),
                               ("3 May 2001", "neg", "DATETIME", "OUT_OF_SCOPE")})

    def test_every_file_of_the_benchmark_is_read(self):
        for name in ("echr_train.json", "echr_dev.json", "echr_test.json"):
            self._write([_doc(name, {"a": []})], name)
        self.assertEqual(sorted(s.sample_id for s in tab.samples(self.root, TABLE)),
                         ["echr_dev.json", "echr_test.json", "echr_train.json"])

    def test_a_mention_whose_offsets_miss_its_text_is_refused(self):
        bad = _m("a", "PERSON", 0, 3, "DIRECT")
        bad["span_text"] = "XYZ"
        self._write([_doc("001-2", {"a": [bad]})])
        with self.assertRaisesRegex(BenchError, "001-2: mention a"):
            list(tab.samples(self.root, TABLE))

    def test_an_unknown_entity_type_stops_with_its_name(self):
        self._write([_doc("001-3", {"a": [_m("a", "SHOE", 0, 3, "DIRECT")]})])
        with self.assertRaisesRegex(BenchError, "'SHOE'"):
            list(tab.samples(self.root, TABLE))

    def test_no_benchmark_file_is_an_error_that_names_the_folder(self):
        with self.assertRaisesRegex(BenchError, "echr_"):
            list(tab.samples(self.root, TABLE))


if __name__ == "__main__":
    unittest.main()
