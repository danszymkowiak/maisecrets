"""The Mendeley synthetic financial-documents adapter (TASK-11.35): one sample per spreadsheet row, its True
Predictions (a Python literal of (start, end, label)) become gold after the text's mojibake is repaired, and the
xlsx is read with the standard library. Made-up rows in the dataset's shape.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from maisecrets_bench.adapters.datasets import mendeley
from maisecrets_bench.domain.labels import LabelTable
from maisecrets_bench.adapters.compose import load_labels as load
from maisecrets_bench.domain.bench_error import BenchError

TABLE = LabelTable("mendeley", {"name": "OUT_OF_SCOPE", "email": "EMAIL", "ssn": "US_SSN"})
RSQUO = chr(0x2019)
MOJIBAKE = RSQUO.encode("utf-8").decode("cp1252")      # the three characters a misread right quote becomes


def _xlsx(rows: list[list[str]]) -> bytes:
    cells = []
    for i, row in enumerate(rows, 1):
        cs = "".join(f'<c r="{chr(65 + j)}{i}" t="inlineStr"><is><t xml:space="preserve">{escape(v)}</t></is></c>'
                     for j, v in enumerate(row))
        cells.append(f'<row r="{i}">{cs}</row>')
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + "".join(cells) + "</sheetData></worksheet>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


HEADER = ["Name", "Credit Card", "Email", "URL", "Phone", "Address", "Company", "SSN", "Text", "True Predictions"]


def _row(text, spans, name="Zed Q", email="zq@example.org", ssn="512-34-5678"):
    return [name, "", email, "", "", "", "", ssn, text, repr(spans)]


class MendeleyTests(unittest.TestCase):
    def test_rows_become_samples_with_gold_of_the_table(self):
        text = "Dear Zed Q, mail zq@example.org about 512-34-5678."
        spans = [(5, 10, "name"), (17, 31, "email"), (38, 49, "ssn")]
        (s,) = list(mendeley.samples([{"_file": "Training_Set", "_row": 2, "I": text, "J": repr(spans)}], TABLE,
                                     mendeley.Stats()))
        self.assertEqual((s.dataset, s.sample_id, s.language), ("mendeley", "Training_Set:2", "en"))
        self.assertEqual([(text[x.start:x.end], x.maisecrets_type) for x in s.spans],
                         [("Zed Q", "OUT_OF_SCOPE"), ("zq@example.org", "EMAIL"), ("512-34-5678", "US_SSN")])

    def test_mojibake_is_repaired_so_the_offsets_land(self):
        # the offsets were taken before a right quote turned into three characters
        clean = f"Auditors{RSQUO} note: mail zq@example.org now."
        broken = clean.replace(RSQUO, MOJIBAKE)
        e = clean.index("zq@")
        (s,) = list(mendeley.samples([{"_file": "t", "_row": 2, "I": broken, "J": repr([(e, e + 14, "email")])}],
                                     TABLE, mendeley.Stats()))
        self.assertEqual(s.text, clean)
        self.assertEqual(s.text[s.spans[0].start:s.spans[0].end], "zq@example.org")

    def test_a_span_outside_the_text_is_dropped_and_counted(self):
        stats = mendeley.Stats()
        (s,) = list(mendeley.samples([{"_file": "t", "_row": 2, "I": "short", "J": "[(0, 99, 'email')]"}], TABLE,
                                     stats))
        self.assertEqual((s.spans, stats.dropped), ([], 1))

    def test_an_unknown_label_stops_with_its_name(self):
        with self.assertRaisesRegex(BenchError, "'shoe_size'"):
            list(mendeley.samples([{"_file": "t", "_row": 2, "I": "abc", "J": "[(0, 1, 'shoe_size')]"}], TABLE,
                                  mendeley.Stats()))

    def test_predictions_are_read_as_a_literal_never_run(self):
        with self.assertRaises(BenchError):
            list(mendeley.samples([{"_file": "t", "_row": 2, "I": "abc", "J": "__import__('os')"}], TABLE,
                                  mendeley.Stats()))

    def test_the_xlsx_reader_skips_the_header_and_keeps_the_columns(self):
        text = "Dear Zed Q."
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "Testing_Set.xlsx"
            p.write_bytes(_xlsx([HEADER, _row(text, [(5, 10, "name")])]))
            (r,) = list(mendeley.read_xlsx(p))
        self.assertEqual((r["_file"], r["_row"], r["I"], r["J"]), ("Testing_Set", 2, text, "[(5, 10, 'name')]"))

    def test_a_sheet_with_other_columns_stops(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.xlsx"
            p.write_bytes(_xlsx([["Text", "Labels"], ["a", "[]"]]))
            with self.assertRaisesRegex(BenchError, "columns"):
                list(mendeley.read_xlsx(p))

    def test_the_table_maps_every_label(self):
        self.assertEqual(set(load("mendeley").mapping), mendeley.LABELS)


if __name__ == "__main__":
    unittest.main()
