"""The one schema every dataset is written in (docs/BENCHMARK.md, One schema): rows are checked before they are
written, and a parquet file reads back the same samples.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import schema
from maisecrets_bench.paths import BenchError
from maisecrets_bench.schema import Sample, Span


def _sample(**kw) -> Sample:
    base = dict(dataset="toy", sample_id="s1", group_id="g1", language="en", text="mail a@example.com now",
                spans=[Span(5, 18, "EMAIL_ADDR", "EMAIL", "pos")], split="dev")
    base.update(kw)
    return Sample(**base)


class ValidateTests(unittest.TestCase):
    def test_a_good_sample_passes(self):
        schema.validate(_sample())

    def test_a_span_outside_the_text_is_refused(self):
        with self.assertRaisesRegex(BenchError, "s1: span 5-99 is outside the text"):
            schema.validate(_sample(spans=[Span(5, 99, "EMAIL_ADDR", "EMAIL", "pos")]))

    def test_an_empty_span_is_refused(self):
        with self.assertRaisesRegex(BenchError, "span 5-5"):
            schema.validate(_sample(spans=[Span(5, 5, "EMAIL_ADDR", "EMAIL", "pos")]))

    def test_a_gold_value_outside_the_three_is_refused(self):
        with self.assertRaisesRegex(BenchError, "gold 'maybe'"):
            schema.validate(_sample(spans=[Span(5, 18, "EMAIL_ADDR", "EMAIL", "maybe")]))

    def test_a_type_maisecrets_does_not_know_is_refused(self):
        with self.assertRaisesRegex(BenchError, "type 'NAME'"):
            schema.validate(_sample(spans=[Span(5, 18, "X", "NAME", "pos")]))

    def test_out_of_scope_is_a_type(self):
        schema.validate(_sample(spans=[Span(0, 4, "VERB", "OUT_OF_SCOPE", "neg")]))

    def test_a_split_other_than_dev_or_check_is_refused(self):
        with self.assertRaisesRegex(BenchError, "split 'train'"):
            schema.validate(_sample(split="train"))

    def test_an_error_never_shows_the_text(self):
        with self.assertRaises(BenchError) as cm:
            schema.validate(_sample(spans=[Span(5, 99, "EMAIL_ADDR", "EMAIL", "pos")]))
        self.assertNotIn("example", str(cm.exception))


class ParquetTests(unittest.TestCase):
    def test_samples_read_back_the_same(self):
        rows = [_sample(), _sample(sample_id="s2", group_id="g2", text="line one\nkey here",
                                   spans=[Span(9, 17, "Token", "SECRET", "pos")], split="check")]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "toy.parquet"
            schema.write(rows, path)
            self.assertEqual(schema.read(path), rows)

    def test_tags_read_back_and_a_file_without_them_reads_as_none(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        rows = [_sample(tags=["format:structured", "locale:us"])]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "toy.parquet"
            schema.write(rows, path)
            self.assertEqual(schema.read(path)[0].tags, ["format:structured", "locale:us"])
            old = pa.schema([f for f in schema.ARROW if f.name != "tags"])
            pq.write_table(pa.Table.from_pylist([{k: v for k, v in r.items() if k != "tags"}
                                                 for r in pq.read_table(path).to_pylist()], schema=old), path)
            self.assertEqual(schema.read(path)[0].tags, [])

    def test_a_sample_id_twice_in_one_dataset_is_refused(self):
        # detections are keyed by (dataset, sample id): a repeat scores one text with another's detections
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(BenchError, "s1"):
            schema.write([_sample(), _sample(text="other mail b@example.com", spans=[])], Path(d) / "toy.parquet")

    def test_write_validates_every_row(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(BenchError):
            schema.write([_sample(split="nope")], Path(d) / "toy.parquet")


if __name__ == "__main__":
    unittest.main()
