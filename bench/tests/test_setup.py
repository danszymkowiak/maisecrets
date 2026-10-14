"""The setup (docs/BENCHMARK.md): every source becomes one parquet file and a manifest entry with its version and
counts; a second run with the same versions writes nothing; a source can be skipped.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench.adapters import compose
from maisecrets_bench.adapters import parquet_store
from maisecrets_bench.application import setup as setup_case
from maisecrets_bench.domain import split
from maisecrets_bench.domain import validgold
from maisecrets_bench.domain.samples import Sample, Span


def _source(name, version, n=3):
    calls = []

    def build():
        calls.append(1)
        for i in range(n):
            yield Sample(name, f"s{i}", f"g{i}", "en", "mail a@b.co", [Span(5, 11, "EMAIL", "EMAIL", "pos")],
                         "dev" if i else "check")
    return setup_case.Source(name, lambda: version, build, lambda: {"dropped": 0}), calls


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def test_each_source_becomes_a_parquet_file_and_a_manifest_entry(self):
        src, _ = _source("toy", "v1")
        compose.setup_run([src], self.out)
        self.assertEqual(len(parquet_store.read(self.out / "toy.parquet")), 3)
        m = json.loads((self.out / "manifest.json").read_text())["datasets"]["toy"]
        self.assertEqual(m["version"], "v1")
        self.assertEqual(m["samples"], 3)
        self.assertEqual(m["spans"], {"pos": 3})
        self.assertEqual(m["split"], {"check": 1, "dev": 2})
        self.assertEqual(m["dropped"], 0)

    def test_a_second_run_with_the_same_version_builds_nothing(self):
        src, calls = _source("toy", "v1")
        compose.setup_run([src], self.out)
        before = (self.out / "toy.parquet").stat().st_mtime_ns
        compose.setup_run([src], self.out)
        self.assertEqual(len(calls), 1)
        self.assertEqual((self.out / "toy.parquet").stat().st_mtime_ns, before)

    def test_a_new_version_rebuilds(self):
        a, _ = _source("toy", "v1")
        b, calls = _source("toy", "v2", n=5)
        compose.setup_run([a], self.out)
        compose.setup_run([b], self.out)
        self.assertEqual(len(calls), 1)
        self.assertEqual(json.loads((self.out / "manifest.json").read_text())["datasets"]["toy"]["samples"], 5)

    def test_other_datasets_stay_in_the_manifest(self):
        a, _ = _source("one", "v1")
        b, _ = _source("two", "v1")
        compose.setup_run([a], self.out)
        compose.setup_run([b], self.out)
        self.assertEqual(set(json.loads((self.out / "manifest.json").read_text())["datasets"]), {"one", "two"})

    def test_invalid_gold_becomes_uncertain_and_the_manifest_counts_it(self):

        def build():
            text = "pay DE12 1234 5678 9012 3456 00 or CH93 0076 2011 6238 5295 7"
            yield Sample("toy", "s0", "g0", "en", text, [Span(4, 31, "iban", "IBAN", "pos"),
                                                        Span(35, 61, "iban", "IBAN", "pos")], "dev")
        compose.setup_run([setup_case.Source("toy", lambda: "v1", build, lambda: {})], self.out)
        spans = parquet_store.read(self.out / "toy.parquet")[0].spans
        self.assertEqual([sp.gold for sp in spans], ["uncertain", "pos"])
        m = json.loads((self.out / "manifest.json").read_text())["datasets"]["toy"]
        self.assertEqual(m["gold"], validgold.REVISION)
        self.assertEqual(m["gold_check"]["IBAN"], {"pos": 2, "valid": 1, "invalid": 1, "trimmed": 0, "negative": 0,
                                                  "retyped": 0})

    def test_an_entry_built_before_the_gold_check_is_built_again(self):
        src, calls = _source("toy", "v1")
        compose.setup_run([src], self.out)
        p = self.out / "manifest.json"
        m = json.loads(p.read_text())
        del m["datasets"]["toy"]["gold"]
        p.write_text(json.dumps(m))
        compose.setup_run([src], self.out)
        self.assertEqual(len(calls), 2)

    def test_the_manifest_records_the_split_salt(self):
        a, _ = _source("one", "v1")
        compose.setup_run([a], self.out)
        self.assertEqual(json.loads((self.out / "manifest.json").read_text())["split_salt"], split.SALT)


if __name__ == "__main__":
    unittest.main()
