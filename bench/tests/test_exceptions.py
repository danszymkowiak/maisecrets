"""Reviewed gold exceptions (TASK-30, bench/gold_exceptions.json): a case no validity rule catches, named by its place
and a hash of its text (never the value), with a verdict and the reason. negative: the label is wrong and the text is
no personal data; uncertain: PII-shaped but invalid; drop: the whole record is broken."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maisecrets_bench import exceptions
from maisecrets_bench.paths import BenchError
from maisecrets_bench.schema import Sample, Span

TEXT = "order SKU 4471-2209 shipped, call 030 1234567"


def sample() -> Sample:
    return Sample("toy", "s1", "s1", "en", TEXT,
                  [Span(10, 19, "PHONE", "PHONE", "pos"), Span(34, 45, "PHONE", "PHONE", "pos")])


def entry(**kw) -> dict:
    base = {"dataset": "toy", "sample_id": "s1", "start": 10, "end": 19, "label": "PHONE",
            "text_sha256": exceptions.digest_text(TEXT[10:19]), "verdict": "negative",
            "rationale": "a product number labelled as a phone"}
    return {**base, **kw}


class ExceptionTests(unittest.TestCase):
    def write(self, entries) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "gold_exceptions.json"
        p.write_text(json.dumps({"entries": entries}), encoding="utf-8")
        return p

    def test_a_negative_verdict_turns_the_span_negative(self):
        (s,), n = exceptions.apply([sample()], exceptions.load(self.write([entry()])))
        self.assertEqual([sp.gold for sp in s.spans], ["neg", "pos"])
        self.assertEqual(n, {"negative": 1})

    def test_uncertain_and_drop(self):
        (s,), _ = exceptions.apply([sample()], exceptions.load(self.write([entry(verdict="uncertain")])))
        self.assertEqual(s.spans[0].gold, "uncertain")
        rows, n = exceptions.apply([sample()], exceptions.load(self.write([entry(verdict="drop")])))
        self.assertEqual((rows, n), ([], {"drop": 1}))

    def test_a_stale_entry_is_refused(self):
        for bad in (entry(sample_id="s9"), entry(start=11), entry(label="EMAIL"),
                    entry(text_sha256=exceptions.digest_text("something else"))):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(BenchError, "stale"):
                    exceptions.apply([sample()], exceptions.load(self.write([bad])))

    def test_an_entry_without_a_rationale_or_with_an_unknown_verdict_is_refused(self):
        for bad in (entry(rationale=""), entry(verdict="maybe"), {k: v for k, v in entry().items() if k != "end"}):
            with self.subTest(bad=bad):
                with self.assertRaises(BenchError):
                    exceptions.load(self.write([bad]))

    def test_entries_of_another_dataset_are_left_for_it(self):
        (s,), n = exceptions.apply([sample()], exceptions.load(self.write([entry(dataset="other")])))
        self.assertEqual([sp.gold for sp in s.spans], ["pos", "pos"])
        self.assertEqual(n, {})

    def test_the_digest_of_a_dataset_changes_with_its_entries_only(self):
        a = exceptions.load(self.write([entry()]))
        b = exceptions.load(self.write([entry(), entry(dataset="other")]))
        self.assertEqual(exceptions.digest(a, "toy"), exceptions.digest(b, "toy"))
        self.assertNotEqual(exceptions.digest(a, "toy"), exceptions.digest(exceptions.load(self.write([])), "toy"))

    def test_the_repository_file_loads(self):
        exceptions.load()


if __name__ == "__main__":
    unittest.main()
