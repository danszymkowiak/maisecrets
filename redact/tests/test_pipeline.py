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


if __name__ == "__main__":
    unittest.main()
