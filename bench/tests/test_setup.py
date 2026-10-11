"""The setup (docs/BENCHMARK.md): every source becomes one parquet file and a manifest entry with its version and
counts; a second run with the same versions writes nothing; a source can be skipped.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import schema, setup
from maisecrets_bench.schema import Sample, Span


def _source(name, version, n=3):
    calls = []

    def build():
        calls.append(1)
        for i in range(n):
            yield Sample(name, f"s{i}", f"g{i}", "en", "mail a@b.co", [Span(5, 11, "EMAIL", "EMAIL", "pos")],
                         "dev" if i else "check")
    return setup.Source(name, lambda: version, build, lambda: {"dropped": 0}), calls


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def test_each_source_becomes_a_parquet_file_and_a_manifest_entry(self):
        src, _ = _source("toy", "v1")
        setup.run([src], self.out)
        self.assertEqual(len(schema.read(self.out / "toy.parquet")), 3)
        m = json.loads((self.out / "manifest.json").read_text())["datasets"]["toy"]
        self.assertEqual(m["version"], "v1")
        self.assertEqual(m["samples"], 3)
        self.assertEqual(m["spans"], {"pos": 3})
        self.assertEqual(m["split"], {"check": 1, "dev": 2})
        self.assertEqual(m["dropped"], 0)

    def test_a_second_run_with_the_same_version_builds_nothing(self):
        src, calls = _source("toy", "v1")
        setup.run([src], self.out)
        before = (self.out / "toy.parquet").stat().st_mtime_ns
        setup.run([src], self.out)
        self.assertEqual(len(calls), 1)
        self.assertEqual((self.out / "toy.parquet").stat().st_mtime_ns, before)

    def test_a_new_version_rebuilds(self):
        a, _ = _source("toy", "v1")
        b, calls = _source("toy", "v2", n=5)
        setup.run([a], self.out)
        setup.run([b], self.out)
        self.assertEqual(len(calls), 1)
        self.assertEqual(json.loads((self.out / "manifest.json").read_text())["datasets"]["toy"]["samples"], 5)

    def test_other_datasets_stay_in_the_manifest(self):
        a, _ = _source("one", "v1")
        b, _ = _source("two", "v1")
        setup.run([a], self.out)
        setup.run([b], self.out)
        self.assertEqual(set(json.loads((self.out / "manifest.json").read_text())["datasets"]), {"one", "two"})

    def test_the_manifest_records_the_split_salt(self):
        a, _ = _source("one", "v1")
        setup.run([a], self.out)
        from maisecrets_bench import split
        self.assertEqual(json.loads((self.out / "manifest.json").read_text())["split_salt"], split.SALT)


if __name__ == "__main__":
    unittest.main()
