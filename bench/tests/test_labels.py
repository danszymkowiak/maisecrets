"""The label table of a dataset (docs/BENCHMARK.md, One schema): every label of a dataset maps to a maisecrets type
or OUT_OF_SCOPE, and an unknown label stops the setup with the label named.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.adapters import files
from maisecrets_bench.domain import labels
from maisecrets_bench.domain.bench_error import BenchError


def _table(text: str) -> labels.LabelTable:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "toy.toml"
        p.write_text(text, encoding="utf-8")
        return compose.load_labels("toy", p)


class LabelTableTests(unittest.TestCase):
    def test_a_label_maps_to_its_type(self):
        t = _table('[labels]\nEMAIL_ADDR = "EMAIL"\nLASTNAME = "OUT_OF_SCOPE"\n')
        self.assertEqual(t.type_of("EMAIL_ADDR"), "EMAIL")
        self.assertEqual(t.type_of("LASTNAME"), "OUT_OF_SCOPE")

    def test_an_unknown_label_stops_with_its_name(self):
        t = _table('[labels]\nEMAIL_ADDR = "EMAIL"\n')
        with self.assertRaisesRegex(BenchError, "toy: label 'SHOE_SIZE' is not in the table"):
            t.type_of("SHOE_SIZE")

    def test_a_table_with_a_type_maisecrets_does_not_know_is_refused(self):
        with self.assertRaisesRegex(BenchError, "toy: label 'X' maps to 'NAME'"):
            _table('[labels]\nX = "NAME"\n')

    def test_every_shipped_table_loads(self):
        for path in sorted(files.LABEL_TABLES.glob("*.toml")):
            with self.subTest(path.name):
                compose.load_labels(path.stem, path)


if __name__ == "__main__":
    unittest.main()
