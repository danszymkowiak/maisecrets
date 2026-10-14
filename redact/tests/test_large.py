"""A large table stays fast (TASK-59, code review 2026-10-14): cell cutting checked every span against every cell edge
and the vote every model span against every rule span, and column hits (TASK-50) make rule spans grow with the rows,
so a 50,000-row CSV or a 10,000-entry password export stalled for minutes.

Run: uv run --project redact python -m unittest discover -s redact/tests
"""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _home  # noqa: E402,F401  first: a temp maisecrets home

from maisecrets_redact import app  # noqa: E402
from maisecrets_redact.pipeline import Span  # noqa: E402

ROWS, LIMIT = 50_000, 10.0


def fake(name: str):
    """A span on every first-column name, and one over the first two cells of every row (name and the placeholder of
    the password the rules found), as the models answered."""
    def find(doc):
        out, at = [], 0
        while True:
            at = doc.text.find("Name", at)
            if at < 0:
                return out
            out += [Span(at, at + 9, "NAME", name), Span(at, doc.text.index("\t", at + 10), "NAME", name)]
            at += 9
    return find


class LargeTableTests(unittest.TestCase):
    def test_a_50000_row_10_column_csv_runs_in_seconds(self):
        d = Path(tempfile.mkdtemp())
        src = d / "big.csv"
        header = "name,password,city,c4,c5,c6,c7,c8,c9,c10"
        src.write_text(header + "\n" + "".join(f"Name{i:05d},testpass-{i},Bern,a,b,c,d,e,f,g\n" for i in range(ROWS)),
                       encoding="utf-8")
        t = time.perf_counter()
        result = app.run_file(src, d / app.output_name(src), model_detectors={"m1": fake("m1"), "m2": fake("m2")},
                              regions=("generic",), interactive=False)
        took = time.perf_counter() - t
        print(f"\n{ROWS} rows x 10 columns: {took:.1f} s", file=sys.stderr)
        self.assertEqual(result.status, "written")
        self.assertEqual((result.counts.get("NAME"), result.counts.get("SECRET")), (ROWS, ROWS))
        self.assertLess(took, LIMIT)


if __name__ == "__main__":
    unittest.main()
