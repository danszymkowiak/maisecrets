"""The pure steps of the pipeline (TASK-34.1): detection merges every detector's spans in order; rendering replaces
each span and lets the first of two overlapping spans cover both."""
from __future__ import annotations

import unittest

from maisecrets_redact import pipeline
from maisecrets_redact.pipeline import Document, Span


def ph(span: Span, value: str) -> str:
    return f"<{span.type}>"


class PipelineTests(unittest.TestCase):
    def test_detect_merges_the_detectors_in_text_order(self):
        doc = Document("x.txt", "mail a@b.ch, call +41 44 000 00 00")
        one = lambda d: [Span(18, 34, "PHONE", "rules")]   # noqa: E731
        two = lambda d: [Span(5, 11, "EMAIL", "model")]    # noqa: E731
        self.assertEqual([s.type for s in pipeline.detect(doc, [one, two])], ["EMAIL", "PHONE"])

    def test_render_replaces_each_span(self):
        doc = Document("x.txt", "mail a@b.ch, call +41 44 000 00 00")
        out = pipeline.render(doc, [Span(5, 11, "EMAIL", "rules"), Span(18, 34, "PHONE", "rules")], ph)
        self.assertEqual(out, "mail <EMAIL>, call <PHONE>")

    def test_overlapping_spans_render_once(self):
        doc = Document("x.txt", "Max Muster, Bahnhofstr. 1")
        out = pipeline.render(doc, [Span(0, 10, "NAME", "m1"), Span(4, 10, "NAME", "m2")], ph)
        self.assertEqual(out, "<NAME>, Bahnhofstr. 1")

    def test_no_span_leaves_the_text(self):
        doc = Document("x.txt", "nothing here")
        self.assertEqual(pipeline.render(doc, [], ph), "nothing here")



class AfterTheRulesTests(unittest.TestCase):
    """The models run after the rules (user, 2026-10-12): they read the text with every rule hit already replaced, and
    their spans map back to the original text; a span's part on a placeholder is dropped, the rules hold it."""

    TEXT = "Konto CH93 0076 2011 6238 5295 7 von Erika Muster, Tel. +41 44 555 01 23"

    def setUp(self):
        iban, phone = "CH93 0076 2011 6238 5295 7", "+41 44 555 01 23"
        i, j = self.TEXT.index(iban), self.TEXT.index(phone)
        self.rules = [Span(i, i + len(iban), "IBAN", "rules"), Span(j, j + len(phone), "PHONE", "rules")]
        self.doc = Document("x.txt", self.TEXT)

    def test_the_models_read_placeholders_where_the_rules_found_values(self):
        m = pipeline.mask(self.doc, self.rules)
        self.assertEqual(m.doc.text, "Konto [IBAN] von Erika Muster, Tel. [PHONE]")

    def test_a_model_span_maps_back_to_the_original_text(self):
        m = pipeline.mask(self.doc, self.rules)
        at = m.doc.text.index("Erika Muster")
        (back,) = m.back([Span(at, at + 12, "NAME", "model", 0.9)])
        self.assertEqual((self.TEXT[back.start:back.end], back.type, back.source, back.score),
                         ("Erika Muster", "NAME", "model", 0.9))

    def test_the_part_of_a_span_on_a_placeholder_is_dropped(self):
        m = pipeline.mask(self.doc, self.rules)
        a, b = m.doc.text.index("[IBAN]"), m.doc.text.index(" Muster") + 7
        self.assertEqual([self.TEXT[s.start:s.end] for s in m.back([Span(a, b, "NAME", "model")])],
                         ["von Erika Muster"])
        p = m.doc.text.index("[PHONE]")
        self.assertEqual(m.back([Span(p, p + 7, "PHONE", "model")]), [])

    def test_without_rule_hits_the_text_is_the_same(self):
        m = pipeline.mask(self.doc, [])
        self.assertIs(m.doc, self.doc)
        self.assertEqual(m.back([Span(0, 5, "X", "m")]), [Span(0, 5, "X", "m")])


if __name__ == "__main__":
    unittest.main()
