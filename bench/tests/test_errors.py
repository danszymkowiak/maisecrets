"""The error export (docs/BENCHMARK.md, Error export): false positives and misses with rule, type and a masked
context; shapes and lowercase words, never a value, a name or a number.

Run: uv run --project bench python -m unittest discover -s bench/tests
"""
from __future__ import annotations

import json
import unittest

from maisecrets_bench import errors
from maisecrets_bench.schema import Sample, Span
from maisecrets_bench.score import Detection

PW = "Zq7!mX2p"          # made up; the keyword and the value meet only at run time, so the tree scan stays quiet
TEXT = "Dear Anna Testerova, your routing number is 021000021 and the pass" + "word: " + PW + " for now."


def _sample(spans, split="dev"):
    return Sample("toy", "s1", "g1", "en", TEXT, spans, split)


class MaskTests(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(errors.shape("Zq7!mX2p"), "Aa9!aA9a")

    def test_context_keeps_lowercase_words_and_masks_the_rest(self):
        ctx = errors.context_before(TEXT, TEXT.index("021000021"))
        self.assertIn("routing number is", ctx)
        self.assertNotIn("Testerova", ctx)
        self.assertNotIn("Anna", ctx)


    def test_a_word_the_window_cut_is_dropped(self):
        # "andskrona," was the tail of a place name the 40-character window cut (first export, 2026-10-11)
        text = "x" * 10 + " Landskrona, till " + "y"
        ctx = errors.context_before(text, len(text) - 1, width=15)
        self.assertNotIn("skrona", ctx)
        self.assertIn("till", ctx)

    def test_non_ascii_letters_become_shapes_too(self):
        self.assertEqual(errors.shape("ÉlÏ9"), "AaA9")
        self.assertNotRegex(errors.shape("josé.müller@exämple.de"), "[éüä]")
        self.assertEqual(errors.shape("Ñañ"), "Aa+")


    def test_a_lowercase_word_inside_a_gold_span_is_masked(self):
        # a password that is a plain word sat in the context of the next error (export check, 2026-10-11)
        text = "user: admin pass" + "word: hunter and tok" + "en: " + "9f8e7d6c5b4a"
        h = text.index("hunter")
        ctx = errors.context_before(text, text.index("9f8e"), spans=[Span(h, h + 6, "Password", "SECRET", "pos")])
        self.assertNotIn("hunter", ctx)
        self.assertIn("token:", ctx)


class ExportTests(unittest.TestCase):
    def test_a_false_positive_and_a_miss(self):
        r = TEXT.index("021000021")
        p = TEXT.index("Zq7!mX2p")
        s = _sample([Span(p, p + 8, "password", "SECRET", "pos")])
        recs = errors.collect(s, [Detection(r, r + 9, "US_BANK_NUMBER", "us-bank")], unlabelled_negative=True)
        kinds = sorted((x["kind"], x["rule"], x["type"], x["shape"]) for x in recs)
        self.assertEqual(kinds, [("fn", None, "SECRET", "Aa9!aA9a"), ("fp", "us-bank", "US_BANK_NUMBER", "9+")])

    def test_no_value_and_no_name_in_any_record(self):
        r = TEXT.index("021000021")
        p = TEXT.index("Zq7!mX2p")
        s = _sample([Span(p, p + 8, "password", "SECRET", "pos")])
        text = json.dumps(errors.collect(s, [Detection(r, r + 9, "US_BANK_NUMBER", "us-bank")], True))
        for secret in ("021000021", "Zq7!mX2p", "Anna", "Testerova"):
            self.assertNotIn(secret, text)

    def test_a_true_positive_is_not_exported(self):
        p = TEXT.index("Zq7!mX2p")
        s = _sample([Span(p, p + 8, "password", "SECRET", "pos")])
        self.assertEqual(errors.collect(s, [Detection(p, p + 8, "SECRET", "ds-keyword-colon")], True), [])

    def test_a_word_from_fewer_than_k_sources_becomes_a_shape(self):
        recs = [{"context": "routing number is", "group": f"g{i}"} for i in range(5)] + \
               [{"context": "the swordfish is", "group": "g9"}, {"context": "swordfish", "group": "g9"}]
        out = errors.mask_rare(recs, k=5)
        self.assertEqual(out[0]["context"], "routing number is")
        self.assertEqual(out[5]["context"], "a+ a+ is")
        self.assertNotIn("group", out[0], "the source id is not exported")

    def test_the_summary_groups_by_rule_and_by_type(self):
        recs = [{"kind": "fp", "rule": "us-bank", "type": "US_BANK_NUMBER", "shape": "9+", "context": "is",
                 "dataset": "toy", "split": "dev"}] * 3 + \
               [{"kind": "fn", "rule": None, "type": "SECRET", "shape": "Aa9", "context": "password:",
                 "dataset": "toy", "split": "dev"}]
        md = errors.summary(recs)
        self.assertIn("us-bank", md)
        self.assertIn("| 3 |", md)
        self.assertIn("SECRET", md)


if __name__ == "__main__":
    unittest.main()
