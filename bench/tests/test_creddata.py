"""The CredData adapter (docs/BENCHMARK.md, CredData): one sample per file, or per window of a large file; one gold
span per meta row (its value, or its lines when no value is given). A fake CredData tree with made-up values.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters.datasets import creddata
from maisecrets_bench.domain.labels import LabelTable
from maisecrets_bench.domain.bench_error import BenchError

HEADER = "Id,FileID,Domain,RepoName,FilePath,LineStart,LineEnd,GroundTruth,ValueStart,ValueEnd,CryptographyKey," \
         "PredefinedPattern,Category\n"
VALUE = "Zq7mXr2Lp9Wt4Kv8"     # made up: the tests check it never shows in output
TABLE = LabelTable("creddata", {"Password": "SECRET", "Token": "SECRET", "PEM Private Key": "SECRET"})


def _tree(d: Path, files: dict, meta: dict) -> Path:
    for rel, text in files.items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
    (d / "meta").mkdir()
    for repo, rows in meta.items():
        (d / "meta" / f"{repo}.csv").write_text(HEADER + "".join(rows), encoding="utf-8")
    return d


def _row(i, repo, path, ls, le, gt, cat="Password", vs="-1", ve="-1"):
    return f"{i},f{i},github.com,{repo},{path},{ls},{le},{gt},{vs},{ve},,,{cat}\n"


class CredDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _small(self):
        text = f"a = 1\npassword = '{VALUE}'\nb = 2\nkey = x\n-----BEGIN\nAAAA\n-----END\n"
        return _tree(self.root, {"data/r1/src/f1.py": text}, {"r1": [
            _row(1, "r1", "data/r1/src/f1.py", 2, 2, "T", vs="12", ve="28"),
            _row(2, "r1", "data/r1/src/f1.py", 2, 2, "F"),
            _row(3, "r1", "data/r1/src/f1.py", 4, 4, "X", cat="Token"),
            _row(4, "r1", "data/r1/src/f1.py", 1, 1, "F"),
            _row(5, "r1", "data/r1/src/f1.py", 5, 7, "T", cat="PEM Private Key"),
        ]})

    def test_one_sample_per_file_and_one_span_per_meta_row(self):
        (s,) = list(creddata.samples(self._small(), TABLE))
        self.assertEqual((s.dataset, s.group_id, s.language), ("creddata", "r1", "und"))
        spans = {(s.text[sp.start:sp.end], sp.gold) for sp in s.spans}
        self.assertIn((VALUE, "pos"), spans, "a row with a value span marks the value")
        self.assertIn((f"password = '{VALUE}'", "neg"), spans, "a row without one marks its line")
        self.assertIn(("key = x", "uncertain"), spans)
        self.assertIn(("-----BEGIN\nAAAA\n-----END", "pos"), spans, "a multi-line row is one span")
        self.assertEqual(len(s.spans), 5)
        self.assertEqual({sp.maisecrets_type for sp in s.spans}, {"SECRET"})
        self.assertIn(s.split, ("dev", "check"))

    def test_the_spans_account_for_every_meta_row(self):
        root = self._small()
        golds = [sp.gold for s in creddata.samples(root, TABLE) for sp in s.spans]
        rows = creddata.count_rows(root)
        self.assertEqual((golds.count("pos"), golds.count("neg"), golds.count("uncertain")),
                         (rows["T"], rows["F"], rows["X"]))

    def test_a_large_file_becomes_windows_around_its_labelled_lines(self):
        lines = [f"line {i}" for i in range(1, 1001)]
        lines[99] = f"token = {VALUE}"
        lines[899] = f"token = {VALUE}"
        _tree(self.root, {"data/r2/big.txt": "\n".join(lines)}, {"r2": [
            _row(1, "r2", "data/r2/big.txt", 100, 100, "T", cat="Token", vs="8", ve="24"),
            _row(2, "r2", "data/r2/big.txt", 900, 900, "F", cat="Token")]})
        out = list(creddata.samples(self.root, TABLE, max_bytes=100, context=5))
        self.assertEqual(len(out), 2)
        first, second = out
        self.assertEqual(first.text.split("\n")[5], f"token = {VALUE}", "line 100 sits after 5 lines of context")
        self.assertEqual([(first.text[sp.start:sp.end], sp.gold) for sp in first.spans], [(VALUE, "pos")])
        self.assertEqual([(second.text[sp.start:sp.end], sp.gold) for sp in second.spans],
                         [(f"token = {VALUE}", "neg")])
        self.assertEqual(first.group_id, second.group_id)
        self.assertNotEqual(first.sample_id, second.sample_id)

    def test_overlapping_windows_merge(self):
        lines = [f"line {i}" for i in range(1, 101)]
        _tree(self.root, {"data/r3/big.txt": "\n".join(lines)}, {"r3": [
            _row(1, "r3", "data/r3/big.txt", 40, 40, "T"), _row(2, "r3", "data/r3/big.txt", 44, 44, "F")]})
        (s,) = list(creddata.samples(self.root, TABLE, max_bytes=10, context=5))
        self.assertEqual([(s.text[sp.start:sp.end], sp.gold) for sp in s.spans],
                         [("line 40", "pos"), ("line 44", "neg")])

    def test_an_empty_labelled_line_still_gets_a_span(self):
        _tree(self.root, {"data/r5/a.txt": "x\n\ny\n"}, {"r5": [_row(1, "r5", "data/r5/a.txt", 2, 2, "F")]})
        (s,) = list(creddata.samples(self.root, TABLE))
        (sp,) = s.spans
        self.assertEqual((sp.start, sp.end), (2, 3), "the empty line 2 is marked by its line break")

    def test_an_unknown_category_stops_with_its_name(self):
        _tree(self.root, {"data/r4/a.txt": "x\n"}, {"r4": [_row(1, "r4", "data/r4/a.txt", 1, 1, "F", cat="Shoe")]})
        with self.assertRaisesRegex(BenchError, "'Shoe'"):
            list(creddata.samples(self.root, TABLE))

    def test_nothing_it_prints_or_raises_shows_a_value(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            list(creddata.samples(self._small(), TABLE))
            creddata.count_rows(self.root)
        self.assertNotIn(VALUE, out.getvalue())


if __name__ == "__main__":
    unittest.main()
